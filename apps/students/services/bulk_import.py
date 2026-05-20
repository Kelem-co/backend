import io
import pandas as pd
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from accounts.models import User
from students.models import Student, Parent, ParentStudentLink
from academics.models import Section
from branches.models import Branch
from organizations.models import Organization

class ParentBulkImportService:
    def __init__(self, file_content, file_name, organization_id, branch_id):
        self.file_content = file_content
        self.file_name = file_name
        self.organization_id = organization_id
        self.branch_id = branch_id
        self.errors = []

    def run(self) -> tuple[bool, list[dict]]:
        # 1. Parse File
        try:
            if self.file_name.endswith('.csv'):
                data = io.StringIO(self.file_content.decode('utf-8'))
                df = pd.read_csv(data)
            elif self.file_name.endswith(('.xls', '.xlsx')):
                data = io.BytesIO(self.file_content)
                df = pd.read_excel(data)
            else:
                return False, [{"row": 0, "errors": {"file": ["Unsupported file format. Please upload CSV or Excel."]}}]
        except Exception as e:
            return False, [{"row": 0, "errors": {"file": [f"Failed to parse file: {str(e)}"]}}]

        # Normalize columns
        df.columns = [str(c).strip().lower() for c in df.columns]

        required_columns = ["name", "email", "phone_number"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, [{
                "row": 0,
                "errors": {
                    "columns": [f"Missing required columns: {', '.join(missing_columns)}"]
                }
            }]

        df = df.where(pd.notnull(df), None)

        try:
            with transaction.atomic():
                try:
                    org = Organization.objects.get(id=self.organization_id)
                except Organization.DoesNotExist:
                    return False, [{"row": 0, "errors": {"organization": ["Organization not found."]}}]

                try:
                    branch = Branch.objects.get(id=self.branch_id, organization=org)
                except Branch.DoesNotExist:
                    return False, [{"row": 0, "errors": {"branch": ["Branch not found or does not belong to organization."]}}]

                seen_emails = set()
                seen_phones = set()

                for index, row in df.iterrows():
                    row_num = index + 2
                    row_errors = {}

                    name = str(row.get("name")).strip() if row.get("name") is not None else ""
                    email = str(row.get("email")).strip() if row.get("email") is not None else ""
                    phone_number = str(row.get("phone_number")).strip() if row.get("phone_number") is not None else ""
                    
                    father_name = str(row.get("father_name")).strip() if row.get("father_name") is not None else ""
                    grandfather_name = str(row.get("grandfather_name")).strip() if row.get("grandfather_name") is not None else ""
                    secondary_phone_number = str(row.get("secondary_phone_number")).strip() if row.get("secondary_phone_number") is not None else ""
                    occupation = str(row.get("occupation")).strip() if row.get("occupation") is not None else ""
                    work_address = str(row.get("work_address")).strip() if row.get("work_address") is not None else ""
                    emergency_contact_name = str(row.get("emergency_contact_name")).strip() if row.get("emergency_contact_name") is not None else ""
                    emergency_contact_phone = str(row.get("emergency_contact_phone")).strip() if row.get("emergency_contact_phone") is not None else ""

                    if not name:
                        row_errors["name"] = ["Name is required."]

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

                    if not phone_number:
                        row_errors["phone_number"] = ["Phone number is required."]
                    else:
                        if phone_number in seen_phones:
                            row_errors["phone_number"] = ["Duplicate phone number in the sheet."]
                        else:
                            seen_phones.add(phone_number)

                    if row_errors:
                        self.errors.append({"row": row_num, "errors": row_errors})
                        continue

                    # Check if User already exists
                    existing_user = User.objects.filter(email__iexact=email).first()
                    
                    if existing_user:
                        if existing_user.role != User.Role.PARENT:
                            row_errors["email"] = [f"A user with this email exists but is not a Parent (role: {existing_user.role})."]
                            self.errors.append({"row": row_num, "errors": row_errors})
                            continue
                        
                        # Existing parent user - update phone if needed and reuse profile
                        if existing_user.phone_number != phone_number:
                            # Verify new phone is not used by another user
                            if User.objects.exclude(id=existing_user.id).filter(phone_number=phone_number).exists():
                                row_errors["phone_number"] = ["This phone number is already registered to another user."]
                                self.errors.append({"row": row_num, "errors": row_errors})
                                continue
                            existing_user.phone_number = phone_number
                            existing_user.save()
                        
                        parent_profile, _ = Parent.objects.get_or_create(user=existing_user)
                    else:
                        # Ensure phone is not registered to another user
                        if User.objects.filter(phone_number=phone_number).exists():
                            row_errors["phone_number"] = ["This phone number is already registered to another user."]
                            self.errors.append({"row": row_num, "errors": row_errors})
                            continue

                        # Create brand new Parent User
                        existing_user = User.objects.create_user(
                            email=email,
                            name=name,
                            father_name=father_name,
                            grandfather_name=grandfather_name,
                            phone_number=phone_number,
                            role=User.Role.PARENT,
                        )
                        existing_user.set_unusable_password()
                        existing_user.save()
                        
                        parent_profile = Parent.objects.create(user=existing_user)

                    # Update M2M and other details
                    parent_profile.organizations.add(org)
                    parent_profile.branches.add(branch)
                    
                    if secondary_phone_number:
                        parent_profile.secondary_phone_number = secondary_phone_number
                    if occupation:
                        parent_profile.occupation = occupation
                    if work_address:
                        parent_profile.work_address = work_address
                    if emergency_contact_name:
                        parent_profile.emergency_contact_name = emergency_contact_name
                    if emergency_contact_phone:
                        parent_profile.emergency_contact_phone = emergency_contact_phone
                    
                    parent_profile.save()

                if self.errors:
                    raise transaction.Rollback()

        except Exception as e:
            if not self.errors:
                self.errors.append({"row": 0, "errors": {"server": [f"Internal error: {str(e)}"]}})
            return False, self.errors

        if self.errors:
            return False, self.errors

        return True, []


class StudentBulkImportService:
    def __init__(self, file_content, file_name, organization_id, branch_id):
        self.file_content = file_content
        self.file_name = file_name
        self.organization_id = organization_id
        self.branch_id = branch_id
        self.errors = []

    def run(self) -> tuple[bool, list[dict]]:
        # 1. Parse File
        try:
            if self.file_name.endswith('.csv'):
                data = io.StringIO(self.file_content.decode('utf-8'))
                df = pd.read_csv(data)
            elif self.file_name.endswith(('.xls', '.xlsx')):
                data = io.BytesIO(self.file_content)
                df = pd.read_excel(data)
            else:
                return False, [{"row": 0, "errors": {"file": ["Unsupported file format. Please upload CSV or Excel."]}}]
        except Exception as e:
            return False, [{"row": 0, "errors": {"file": [f"Failed to parse file: {str(e)}"]}}]

        # Normalize columns
        df.columns = [str(c).strip().lower() for c in df.columns]

        required_columns = ["first_name", "last_name", "gender", "date_of_birth", "roll_no", "section_name", "admission_date"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, [{
                "row": 0,
                "errors": {
                    "columns": [f"Missing required columns: {', '.join(missing_columns)}"]
                }
            }]

        df = df.where(pd.notnull(df), None)

        try:
            with transaction.atomic():
                try:
                    org = Organization.objects.get(id=self.organization_id)
                except Organization.DoesNotExist:
                    return False, [{"row": 0, "errors": {"organization": ["Organization not found."]}}]

                try:
                    branch = Branch.objects.get(id=self.branch_id, organization=org)
                except Branch.DoesNotExist:
                    return False, [{"row": 0, "errors": {"branch": ["Branch not found or does not belong to organization."]}}]

                seen_roll_numbers = set()

                for index, row in df.iterrows():
                    row_num = index + 2
                    row_errors = {}

                    first_name = str(row.get("first_name")).strip() if row.get("first_name") is not None else ""
                    last_name = str(row.get("last_name")).strip() if row.get("last_name") is not None else ""
                    gender_raw = str(row.get("gender")).strip().upper() if row.get("gender") is not None else ""
                    date_of_birth_raw = row.get("date_of_birth")
                    roll_no = str(row.get("roll_no")).strip() if row.get("roll_no") is not None else ""
                    section_name = str(row.get("section_name")).strip() if row.get("section_name") is not None else ""
                    grade_name = str(row.get("grade_name")).strip() if row.get("grade_name") is not None else None
                    admission_date_raw = row.get("admission_date")
                    
                    parent_emails_raw = str(row.get("parent_emails")).strip() if row.get("parent_emails") is not None else ""
                    relationship_types_raw = str(row.get("relationship_types")).strip() if row.get("relationship_types") is not None else ""
                    is_primary_contacts_raw = str(row.get("is_primary_contacts")).strip() if row.get("is_primary_contacts") is not None else ""

                    if not first_name:
                        row_errors["first_name"] = ["First name is required."]
                    if not last_name:
                        row_errors["last_name"] = ["Last name is required."]

                    # Validate Gender
                    if gender_raw not in dict(Student.Gender.choices):
                        row_errors["gender"] = [f"Invalid gender. Must be one of: {', '.join(dict(Student.Gender.choices).keys())}."]

                    # Validate Date of Birth
                    date_of_birth = None
                    if date_of_birth_raw is None:
                        row_errors["date_of_birth"] = ["Date of birth is required."]
                    else:
                        try:
                            date_of_birth = pd.to_datetime(date_of_birth_raw).date()
                        except Exception:
                            row_errors["date_of_birth"] = ["Invalid date format. Use YYYY-MM-DD."]

                    # Validate Admission Date
                    admission_date = None
                    if admission_date_raw is None:
                        row_errors["admission_date"] = ["Admission date is required."]
                    else:
                        try:
                            admission_date = pd.to_datetime(admission_date_raw).date()
                        except Exception:
                            row_errors["admission_date"] = ["Invalid date format. Use YYYY-MM-DD."]

                    # Resolve Section
                    section = None
                    if not section_name:
                        row_errors["section_name"] = ["Section name is required."]
                    else:
                        sections_qs = Section.objects.filter(branch=branch, name__iexact=section_name)
                        if grade_name:
                            sections_qs = sections_qs.filter(grade__name__iexact=grade_name)
                        
                        count = sections_qs.count()
                        if count == 0:
                            err_msg = f"Section '{section_name}' not found"
                            if grade_name:
                                err_msg += f" for Grade '{grade_name}'"
                            row_errors["section_name"] = [err_msg + "."]
                        elif count > 1:
                            row_errors["section_name"] = [f"Multiple sections found named '{section_name}'. Please specify 'grade_name' to disambiguate."]
                        else:
                            section = sections_qs.first()

                    # Validate Roll Number within Section/Branch
                    if not roll_no:
                        row_errors["roll_no"] = ["Roll number is required."]
                    else:
                        # Sheet duplicates
                        roll_key = (section.id if section else None, roll_no.lower())
                        if roll_key in seen_roll_numbers:
                            row_errors["roll_no"] = ["Duplicate roll number in this section within the sheet."]
                        else:
                            seen_roll_numbers.add(roll_key)

                            # DB duplicates
                            if section and Student.objects.filter(branch=branch, current_section=section, roll_no__iexact=roll_no).exists():
                                row_errors["roll_no"] = ["Roll number already exists in this section."]

                    # Parse Parent links if provided
                    parent_links_to_create = []
                    if parent_emails_raw:
                        emails = [e.strip() for e in parent_emails_raw.split(",") if e.strip()]
                        relationships = [r.strip().upper() for r in relationship_types_raw.split(",") if r.strip()]
                        primaries = [p.strip().lower() in ("true", "1", "yes") for p in is_primary_contacts_raw.split(",") if p.strip()]

                        for i, email in enumerate(emails):
                            try:
                                validate_email(email)
                            except ValidationError:
                                if "parent_emails" not in row_errors:
                                    row_errors["parent_emails"] = []
                                row_errors["parent_emails"].append(f"Invalid email: {email}")
                                continue

                            parent_profile = Parent.objects.filter(user__email__iexact=email).first()
                            if not parent_profile:
                                if "parent_emails" not in row_errors:
                                    row_errors["parent_emails"] = []
                                row_errors["parent_emails"].append(f"Parent with email '{email}' not found. Please import parents first.")
                                continue
                            
                            # Ensure parent belongs to the student's org/branch
                            if not parent_profile.organizations.filter(id=self.organization_id).exists() or not parent_profile.branches.filter(id=self.branch_id).exists():
                                if "parent_emails" not in row_errors:
                                    row_errors["parent_emails"] = []
                                row_errors["parent_emails"].append(f"Parent '{email}' exists but is not linked to this organization/branch.")
                                continue

                            rel_type = relationships[i] if i < len(relationships) else "GUARDIAN"
                            if rel_type not in dict(ParentStudentLink.Relationship.choices):
                                rel_type = "OTHER"

                            is_primary = primaries[i] if i < len(primaries) else False
                            
                            parent_links_to_create.append({
                                "parent": parent_profile,
                                "relationship_type": rel_type,
                                "is_primary_contact": is_primary
                            })

                    if row_errors:
                        # Consolidate parent email list messages
                        if "parent_emails" in row_errors:
                            row_errors["parent_emails"] = ["; ".join(row_errors["parent_emails"])]
                        self.errors.append({"row": row_num, "errors": row_errors})
                        continue

                    # Create Student
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
                    )

                    # Create Links
                    for link_data in parent_links_to_create:
                        ParentStudentLink.objects.create(
                            student=student,
                            parent=link_data["parent"],
                            relationship_type=link_data["relationship_type"],
                            is_primary_contact=link_data["is_primary_contact"]
                        )

                if self.errors:
                    raise transaction.Rollback()

        except Exception as e:
            if not self.errors:
                self.errors.append({"row": 0, "errors": {"server": [f"Internal error: {str(e)}"]}})
            return False, self.errors

        if self.errors:
            return False, self.errors

        return True, []
