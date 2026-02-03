from django.shortcuts import render, get_object_or_404
from .models import SubjectAssignment, ExamResult
from students.models import Student
from datetime import date
import pandas as pd


def upload_results_view(request, token):
    assignment = get_object_or_404(SubjectAssignment, upload_token=token)
    exam_session = assignment.exam_session
    feedback = None  # message for the template

    # --- Step 1: Check if uploads are allowed ---
    if exam_session.is_locked:
        feedback = {"type": "error", "message": "This exam session is locked. Uploads disabled."}
    elif date.today() > assignment.upload_deadline:
        feedback = {"type": "error", "message": "Upload closed. Deadline passed."}

    # --- Step 2: Handle Excel upload ---
    if request.method == "POST" and not feedback:
        file = request.FILES.get("file")

        try:
            # --- Read Excel file ---
            df = pd.read_excel(file)

            # --- Normalize headers (case-insensitive, trim, and underscores) ---
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

            print("DEBUG: Excel Columns →", list(df.columns))  # <-- useful for debugging

            # --- Check required columns ---
            if "admission_number" not in df.columns or "score" not in df.columns:
                feedback = {
                    "type": "error",
                    "message": "Excel must have 'Admission Number' and 'Score' columns."
                }
            else:
                count_uploaded = 0
                missing_students = []

                # --- Process each student record ---
                for _, row in df.iterrows():
                    admission_number = str(row["admission_number"]).strip()
                    score = row["score"]

                    if pd.isna(admission_number) or pd.isna(score):
                        continue  # skip blank rows

                    # --- Find the student by admission number ---
                    student = Student.objects.filter(admission_number=admission_number).first()
                    if not student:
                        missing_students.append(admission_number)
                        continue

                    # --- Save or update score ---
                    ExamResult.objects.update_or_create(
                        student=student,
                        assignment=assignment,
                        defaults={"score": score},
                    )
                    count_uploaded += 1

                # --- Mark assignment as uploaded ---
                assignment.is_uploaded = True
                assignment.save()

                # --- Build success message ---
                message = f"✅ {count_uploaded} results uploaded successfully!"
                if missing_students:
                    message += f" ⚠️ {len(missing_students)} student(s) not found: {', '.join(missing_students[:5])}"
                    if len(missing_students) > 5:
                        message += " ..."

                feedback = {"type": "success", "message": message}

        except Exception as e:
            feedback = {"type": "error", "message": f"Error processing file: {str(e)}"}

    # --- Step 3: Render Template ---
    return render(
        request,
        "results/upload_form.html",
        {"assignment": assignment, "feedback": feedback}
    )
