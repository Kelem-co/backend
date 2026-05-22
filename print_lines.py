# ruff: noqa: E501
"""Scratch file for inspecting generated line numbers during local debugging."""

script = """def run_no_catch(self):
    from django.db import transaction
    import pandas as pd
    import io

    data = io.StringIO(self.file_content.decode('utf-8'))
    df = pd.read_csv(data)
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.fillna('')

    seen_roll_numbers = set()
    org = Organization.objects.get(id=self.organization_id)
    branch = Branch.objects.get(id=self.branch_id, organization=org)

    for index, row in df.iterrows():
        row_num = index + 2
        row_errors = {}

        first_name = str(row.get('first_name')).strip() if row.get('first_name') is not None else ''
        last_name = str(row.get('last_name')).strip() if row.get('last_name') is not None else ''
        gender_raw = str(row.get('gender')).strip().upper() if row.get('gender') is not None else ''
        date_of_birth_raw = row.get('date_of_birth')
        roll_no = str(row.get('roll_no')).strip() if row.get('roll_no') is not None else ''
        section_name = str(row.get('section_name')).strip() if row.get('section_name') is not None else ''
        grade_name = str(row.get('grade_name')).strip() if row.get('grade_name') is not None else None
        admission_date_raw = row.get('admission_date')

        parent_emails_raw = str(row.get('parent_emails')).strip() if row.get('parent_emails') is not None else ''
        relationship_types_raw = str(row.get('relationship_types')).strip() if row.get('relationship_types') is not None else ''
        is_primary_contacts_raw = str(row.get('is_primary_contacts')).strip() if row.get('is_primary_contacts') is not None else ''

        if not first_name: row_errors['first_name'] = ['First name is required.']
        if not last_name: row_errors['last_name'] = ['Last name is required.']

        date_of_birth = None
        try:
            date_of_birth = pd.to_datetime(date_of_birth_raw).date()
        except Exception:
            row_errors['date_of_birth'] = ['Invalid date format. Use YYYY-MM-DD.']

        admission_date = None
        if admission_date_raw is None or str(admission_date_raw).strip() == '':
            from datetime import date
            admission_date = date.today()
        else:
            try:
                admission_date = pd.to_datetime(admission_date_raw).date()
            except Exception:
                row_errors['admission_date'] = ['Invalid date format. Use YYYY-MM-DD.']

        section = None

        if not roll_no:
            import uuid
            roll_no = f'STU-{uuid.uuid4().hex[:8].upper()}'

        parent_links_to_create = []
        if parent_emails_raw:
            pass

        student = None
        from students.models import Student
        student = Student.objects.create(
            organization=org,
            branch=branch,
            first_name=first_name,
            last_name=last_name,
            gender=gender_raw,
            date_of_birth=date_of_birth,
            roll_no=roll_no,
            current_section=section,
            admission_date=admission_date,
        )"""

LINE_NUMBERS = [f"{i:2d}: {line}" for i, line in enumerate(script.split("\n"), 1)]
