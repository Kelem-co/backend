import io
import pandas as pd
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from accounts.models import User
from teachers.models import Teacher
from branches.models import Branch
from organizations.models import Organization

class TeacherBulkImportService:
    def __init__(self, file_content, file_name, organization_id, branch_id):
        self.file_content = file_content
        self.file_name = file_name
        self.organization_id = organization_id
        self.branch_id = branch_id
        self.errors = []  # List of dicts: {"row": int, "errors": dict}

    def run(self) -> tuple[bool, list[dict]]:
        # 1. Parse File using Pandas
        try:
            if self.file_name.endswith('.csv'):
                # CSV files can be parsed from bytes via string decoding
                data = io.StringIO(self.file_content.decode('utf-8'))
                df = pd.read_csv(data)
            elif self.file_name.endswith(('.xls', '.xlsx')):
                # Excel files can be parsed from bytes via BytesIO
                data = io.BytesIO(self.file_content)
                df = pd.read_excel(data)
            else:
                return False, [{"row": 0, "errors": {"file": ["Unsupported file format. Please upload CSV or Excel."]}}]
        except Exception as e:
            return False, [{"row": 0, "errors": {"file": [f"Failed to parse file: {str(e)}"]}}]

        # Trim column names
        df.columns = [str(c).strip().lower() for c in df.columns]

        required_columns = ["name", "email", "employee_id", "joining_date"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, [{
                "row": 0,
                "errors": {
                    "columns": [f"Missing required columns: {', '.join(missing_columns)}"]
                }
            }]

        # Replace NaN values with None/empty string for easier processing
        df = df.where(pd.notnull(df), None)

        try:
            with transaction.atomic():
                # Verify that organization and branch exist and match
                try:
                    org = Organization.objects.get(id=self.organization_id)
                except Organization.DoesNotExist:
                    return False, [{"row": 0, "errors": {"organization": ["Organization not found."]}}]

                try:
                    branch = Branch.objects.get(id=self.branch_id, organization=org)
                except Branch.DoesNotExist:
                    return False, [{"row": 0, "errors": {"branch": ["Branch not found or does not belong to organization."]}}]

                # Temporary memory tracking to prevent duplicates within the same sheet
                seen_emails = set()
                seen_employee_ids = set()

                for index, row in df.iterrows():
                    row_num = index + 2  # 1-indexed plus header row is row 2
                    row_errors = {}

                    # Extract values
                    name = str(row.get("name")).strip() if row.get("name") is not None else ""
                    email = str(row.get("email")).strip() if row.get("email") is not None else ""
                    employee_id = str(row.get("employee_id")).strip() if row.get("employee_id") is not None else ""
                    joining_date_raw = row.get("joining_date")
                    
                    father_name = str(row.get("father_name")).strip() if row.get("father_name") is not None else ""
                    grandfather_name = str(row.get("grandfather_name")).strip() if row.get("grandfather_name") is not None else ""
                    phone_number = str(row.get("phone_number")).strip() if row.get("phone_number") is not None else ""
                    specialization = str(row.get("specialization")).strip() if row.get("specialization") is not None else ""
                    bio = str(row.get("bio")).strip() if row.get("bio") is not None else ""

                    # Validate Name
                    if not name:
                        row_errors["name"] = ["Name is required."]

                    # Validate Email
                    if not email:
                        row_errors["email"] = ["Email is required."]
                    else:
                        try:
                            validate_email(email)
                        except ValidationError:
                            row_errors["email"] = ["Invalid email format."]
                        
                        if email.lower() in seen_emails:
                            row_errors["email"] = ["Duplicate email in the sheet."]
                        else:
                            seen_emails.add(email.lower())
                            
                            # Check database uniqueness
                            if User.objects.filter(email__iexact=email).exists():
                                row_errors["email"] = ["A user with this email already exists."]

                    # Validate Employee ID
                    if not employee_id:
                        row_errors["employee_id"] = ["Employee ID is required."]
                    else:
                        if employee_id.lower() in seen_employee_ids:
                            row_errors["employee_id"] = ["Duplicate Employee ID in the sheet."]
                        else:
                            seen_employee_ids.add(employee_id.lower())
                            
                            # Check database uniqueness
                            if Teacher.objects.filter(employee_id__iexact=employee_id).exists():
                                row_errors["employee_id"] = ["Teacher with this Employee ID already exists."]

                    # Validate Joining Date
                    joining_date = None
                    if joining_date_raw is None:
                        row_errors["joining_date"] = ["Joining date is required."]
                    else:
                        try:
                            joining_date = pd.to_datetime(joining_date_raw).date()
                        except Exception:
                            row_errors["joining_date"] = ["Invalid date format. Use YYYY-MM-DD."]

                    # Validate Phone Number uniqueness if provided
                    if phone_number:
                        if User.objects.filter(phone_number=phone_number).exists():
                            row_errors["phone_number"] = ["A user with this phone number already exists."]

                    # If errors in this row, skip creation and log errors
                    if row_errors:
                        self.errors.append({"row": row_num, "errors": row_errors})
                        continue

                    # Create User
                    user = User.objects.create_user(
                        email=email,
                        name=name,
                        father_name=father_name,
                        grandfather_name=grandfather_name,
                        phone_number=phone_number if phone_number else None,
                        role=User.Role.TEACHER,
                    )
                    user.set_unusable_password()
                    user.save()

                    # Create Teacher Profile
                    Teacher.objects.create(
                        user=user,
                        organization=org,
                        branch=branch,
                        employee_id=employee_id,
                        joining_date=joining_date,
                        specialization=specialization,
                        bio=bio
                    )

                if self.errors:
                    # Rollback transaction
                    raise transaction.Rollback()

        except Exception as e:
            if not self.errors:
                self.errors.append({"row": 0, "errors": {"server": [f"Internal error: {str(e)}"]}})
            return False, self.errors

        if self.errors:
            return False, self.errors

        return True, []
