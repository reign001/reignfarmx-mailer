from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app
)

from app.forms.import_form import ImportForm
from app.services.import_service import ImportService

import os
import json
import secrets


import_center_bp = Blueprint(
    "import_center",
    __name__,
    url_prefix="/imports"
)


# ============================================================
# SERVER-SIDE IMPORT DATA STORAGE
# ============================================================

def get_import_storage():
    """
    Returns the directory used to temporarily store
    import previews and reports.
    """

    storage_dir = os.path.join(
        current_app.instance_path,
        "import_data"
    )

    os.makedirs(
        storage_dir,
        exist_ok=True
    )

    return storage_dir


def save_import_data(data):
    """
    Save import data on the server and return
    a unique ID.
    """

    data_id = secrets.token_urlsafe(32)

    file_path = os.path.join(
        get_import_storage(),
        f"{data_id}.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False
        )

    return data_id


def load_import_data(data_id):
    """
    Load import data from server storage.
    """

    if not data_id:
        return None

    file_path = os.path.join(
        get_import_storage(),
        f"{data_id}.json"
    )

    if not os.path.exists(file_path):
        return None

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def delete_import_data(data_id):
    """
    Delete temporary import data.
    """

    if not data_id:
        return

    file_path = os.path.join(
        get_import_storage(),
        f"{data_id}.json"
    )

    if os.path.exists(file_path):
        os.remove(file_path)


# ============================================================
# UPLOAD
# ============================================================

@import_center_bp.route("/", methods=["GET", "POST"])
def upload():

    form = ImportForm()

    if form.validate_on_submit():

        file = form.csv_file.data

        try:

            preview = ImportService.preview(file)

            print("=" * 80)
            print("IMPORT PREVIEW")
            print("=" * 80)
            print(preview)
            print("=" * 80)

            # Print validation summary
            if "summary" in preview:

                print("SUMMARY")
                print(preview["summary"])

            # Print validation issues
            print("=" * 80)
            print("VALIDATION ISSUES")
            print("=" * 80)

            for index, row in enumerate(
                preview.get("rows", []),
                start=1
            ):

                if row.get("status") != "Valid":

                    print(
                        f"Row {index}: "
                        f"{row.get('company_name', 'Unknown')} "
                        f"-> "
                        f"{row.get('reason', 'Unknown error')}"
                    )

            print("=" * 80)

            # ------------------------------------------------
            # SAVE PREVIEW ON SERVER
            # ------------------------------------------------

            preview_id = save_import_data(preview)

            # ------------------------------------------------
            # STORE ONLY SMALL ID IN SESSION
            # ------------------------------------------------

            session["import_preview_id"] = preview_id

            return redirect(
                url_for("import_center.preview")
            )

        except Exception as e:

            import traceback

            traceback.print_exc()

            flash(
                f"Import failed: {str(e)}",
                "danger"
            )

    return render_template(
        "import_center/upload.html",
        form=form
    )


# ============================================================
# PREVIEW
# ============================================================

@import_center_bp.route("/preview")
def preview():

    preview_id = session.get(
        "import_preview_id"
    )

    data = load_import_data(
        preview_id
    )

    if not data:

        session.pop(
            "import_preview_id",
            None
        )

        flash(
            "Please upload a CSV first.",
            "warning"
        )

        return redirect(
            url_for("import_center.upload")
        )

    # Normalize summary structure
    if "summary" not in data:

        data["summary"] = {
            "total": data.get("total", 0),
            "valid": data.get("valid", 0),
            "duplicates": data.get("duplicates", 0),
            "invalid": data.get("invalid", 0),
        }

    return render_template(
        "import_center/preview.html",
        preview=data
    )


# ============================================================
# IMPORT DATA
# ============================================================

@import_center_bp.route(
    "/import",
    methods=["POST"]
)
def import_data():

    preview_id = session.get(
        "import_preview_id"
    )

    data = load_import_data(
        preview_id
    )

    if not data:

        session.pop(
            "import_preview_id",
            None
        )

        flash(
            "Nothing to import.",
            "warning"
        )

        return redirect(
            url_for("import_center.upload")
        )

    try:

        report = ImportService.import_records(
            data
        )

        # ------------------------------------------------
        # Delete preview because it is no longer needed
        # ------------------------------------------------

        delete_import_data(
            preview_id
        )

        session.pop(
            "import_preview_id",
            None
        )

        # ------------------------------------------------
        # Store report on server too
        # ------------------------------------------------

        report_id = save_import_data(
            report
        )

        session["import_report_id"] = report_id

        return redirect(
            url_for("import_center.report")
        )

    except Exception as e:

        import traceback

        traceback.print_exc()

        flash(
            f"Import failed: {str(e)}",
            "danger"
        )

        return redirect(
            url_for("import_center.preview")
        )


# ============================================================
# REPORT
# ============================================================

@import_center_bp.route("/report")
def report():

    report_id = session.get(
        "import_report_id"
    )

    report_data = load_import_data(
        report_id
    )

    if not report_data:

        session.pop(
            "import_report_id",
            None
        )

        return redirect(
            url_for("import_center.upload")
        )

    return render_template(
        "import_center/report.html",
        report=report_data
    )