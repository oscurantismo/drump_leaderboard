from flask import Blueprint, request, jsonify, send_file, render_template_string
import json, os
from utils.timeutils import gmt4_now
from werkzeug.utils import secure_filename
from utils.logging import log_event
from apscheduler.schedulers.background import BackgroundScheduler

subscription_routes = Blueprint("subscription_routes", __name__)
SUB_PATH = "subscriptions.json"
BACKUP_DIR = "data/subscription_backups"
os.makedirs(BACKUP_DIR, exist_ok=True)


def auto_backup_subscriptions():
    if not os.path.exists(SUB_PATH):
        print("⚠️ subscriptions.json not found, skipping backup.")
        return

    try:
        timestamp = gmt4_now().strftime("%Y%m%d-%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"auto_daily_{timestamp}.json")

        with open(SUB_PATH, "r") as f:
            content = f.read()
            json.loads(content)  # Validate
            with open(backup_path, "w") as bkp:
                bkp.write(content)

        log_event(f"✅ subscriptions.json auto-backed up as {backup_path}")

    except Exception as e:
        log_event(f"❌ Failed to auto-backup subscriptions.json: {e}")


def load_subscriptions():
    if not os.path.exists(SUB_PATH):
        return {}
    try:
        with open(SUB_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load subscriptions.json: {e}")
        return {}

def save_subscriptions(data):
    if not isinstance(data, dict):
        raise ValueError("Subscriptions data must be a dictionary")
    with open(SUB_PATH, "w") as f:
        json.dump(data, f, indent=2)

@subscription_routes.route("/subscription-dashboard")
def subscription_dashboard():
    subs = load_subscriptions()
    rows = []
    for uid, info in subs.items():
        rows.append(f"""
            <tr>
                <td>{uid}</td>
                <td>{info.get('username', 'Unknown')}</td>
                <td>{'✅' if info.get('subscribed') else '❌'}</td>
                <td>{info.get('subscribed_at', 'N/A')}</td>
                <td>{'✅' if info.get('opted_out') else '❌'}</td>
            </tr>
        """)

    table = "\n".join(rows)

    # List backup files
    backup_files = sorted(os.listdir(BACKUP_DIR), reverse=True)
    options = "\n".join(
        f'<option value="{fname}">{fname}</option>' for fname in backup_files if fname.endswith(".json")
    )

    return render_template_string("""
        <h2>🔔 User Subscriptions</h2>

        <div style="margin-bottom: 20px;">
            <button onclick="download()">⬇️ Download Current</button>
            <button onclick="document.getElementById('upload').click()">⬆️ Upload New</button>
            <input type="file" id="upload" style="display:none" onchange="upload(event)">
        </div>

        <div style="margin-bottom: 20px;">
            <label><strong>🔄 Restore from Backup:</strong></label>
            <select id="restore-select">
                {{options | safe}}
            </select>
            <button onclick="restoreBackup()">Restore</button>
        </div>

        <table border="1" cellpadding="6" cellspacing="0">
            <tr><th>User ID</th><th>Username</th><th>Subscribed</th><th>Subscribed At</th><th>Opted Out</th></tr>
            {{table | safe}}
        </table>

        <script>
        function download() {
            window.location = "/subscription-backup/download";
        }
        function upload(e) {
            const file = e.target.files[0];
            if (!file) return alert("❌ No file selected.");
            const form = new FormData();
            form.append("file", file);
            fetch("/subscription-backup/upload", {
                method: "POST",
                body: form
            }).then(res => res.json())
              .then(data => {
                  if (data.ok) {
                      alert("✅ Uploaded and saved.");
                      location.reload();
                  } else {
                      alert("❌ Upload error: " + (data.error || "Unknown"));
                  }
              })
              .catch(err => alert("❌ Upload failed: " + err));
        }
        function restoreBackup() {
            const selected = document.getElementById("restore-select").value;
            if (!confirm("Restore backup '" + selected + "'? This will overwrite current subscriptions.")) return;
            fetch("/subscription-backup/restore", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename: selected })
            })
            .then(res => res.json())
            .then(data => {
                if (data.ok) {
                    alert("✅ Restored from backup.");
                    location.reload();
                } else {
                    alert("❌ Failed to restore: " + (data.error || "Unknown"));
                }
            });
        }
        </script>
    """, table=table, options=options)


@subscription_routes.route("/subscription-backup/download")
def download_subscription_backup():
    if not os.path.exists(SUB_PATH):
        return "❌ subscriptions.json not found.", 404
    return send_file(SUB_PATH, as_attachment=True)


@subscription_routes.route("/subscription-backup/upload", methods=["POST"])
def upload_subscription_backup():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        # Read & validate JSON first
        content = file.read().decode("utf-8")
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("Uploaded file must contain a JSON object")

        # Backup current
        if os.path.exists(SUB_PATH):
            timestamp = gmt4_now().strftime("%Y%m%d-%H%M%S")
            backup_path = os.path.join(BACKUP_DIR, f"auto_{timestamp}.json")
            with open(SUB_PATH, "r") as old:
                with open(backup_path, "w") as bkp:
                    bkp.write(old.read())
            log_event(f"📦 Backup created before manual subscription upload: {backup_path}")

        # Save new version
        with open(SUB_PATH, "w") as f:
            f.write(content)

        log_event("🆕 subscriptions.json manually uploaded and saved")
        return jsonify({"ok": True})

    except Exception as e:
        log_event(f"❌ Subscription upload failed: {e}")
        return jsonify({"error": f"Invalid JSON or upload error: {e}"}), 400


@subscription_routes.route("/subscription-backup/restore", methods=["POST"])
def restore_backup():
    data = request.get_json()
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "Missing filename"}), 400

    path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "Backup not found"}), 404

    try:
        with open(path, "r") as f:
            parsed = json.load(f)
        if not isinstance(parsed, dict):
            raise ValueError("Backup file is not a valid dict")

        # Backup current before restoring
        if os.path.exists(SUB_PATH):
            timestamp = gmt4_now().strftime("%Y%m%d-%H%M%S")
            with open(SUB_PATH, "r") as cur, open(os.path.join(BACKUP_DIR, f"auto_before_restore_{timestamp}.json"), "w") as bkp:
                bkp.write(cur.read())

        # Restore
        with open(SUB_PATH, "w") as f:
            json.dump(parsed, f, indent=2)

        log_event(f"♻️ subscriptions.json restored from backup: {filename}")
        return jsonify({"ok": True})
    except Exception as e:
        log_event(f"❌ Failed to restore subscription backup '{filename}': {e}")
        return jsonify({"error": f"Failed to restore: {e}"}), 500


