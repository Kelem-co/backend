erDiagram
User {
  uuid id pk
  varchar password 
  timestamp_with_time_zone last_login 
  boolean is_superuser 
  varchar first_name 
  varchar last_name 
  boolean is_staff 
  boolean is_active 
  timestamp_with_time_zone date_joined 
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  varchar email 
  varchar name 
  varchar father_name 
  varchar grandfather_name 
  varchar role 
  varchar phone_number 
  varchar address 
  timestamp_with_time_zone verified_at 
}
ApprovalLoginToken {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid user_id 
  varchar token_hash 
  timestamp_with_time_zone expires_at 
  timestamp_with_time_zone used_at 
}
ParentLoginOTP {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid user_id 
  varchar phone_number 
  varchar code_hash 
  timestamp_with_time_zone expires_at 
  timestamp_with_time_zone used_at 
  smallint failed_attempts 
}
Organization {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid owner_id 
  varchar name 
  varchar trade_name 
  varchar tin_number 
  varchar license_no 
  varchar client_full_name 
  text business_address 
  varchar business_phone_number 
  varchar client_phone_number 
  uuid business_license_image_id 
  varchar status 
  varchar verification_status 
  timestamp_with_time_zone verification_checked_at 
  varchar verification_failure_reason 
  varchar verification_match_source 
  varchar verified_name 
  varchar verified_license_no 
  varchar verified_tin_number 
}
School {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  varchar name 
  text description 
  varchar country 
  varchar contact_email 
  varchar contact_phone 
  uuid logo_id 
  varchar website 
  varchar status 
}
Branch {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid school_id 
  varchar name 
  text address 
  varchar city 
  varchar region 
  varchar contact_phone 
  varchar contact_email 
  varchar status 
}
BranchAdmin {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid branch_id 
  uuid user_id 
  varchar emergency_contact_name 
  varchar emergency_contact_phone 
  varchar role_title 
  varchar qualification 
  varchar status 
  timestamp_with_time_zone last_login 
}
AcademicYear {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid branch_id 
  varchar name 
  date start_date 
  date end_date 
  boolean is_current 
}
Grade {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid branch_id 
  varchar name 
  integer level 
}
Section {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid branch_id 
  uuid grade_id 
  uuid academic_year_id 
  varchar name 
}
Subject {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid branch_id 
  uuid grade_id 
  varchar name 
  varchar code 
}
GradeSubject {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid grade_id 
  uuid subject_id 
}
CalendarDocument {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid branch_id 
  uuid academic_year_id 
  uuid media_file_id 
}
Parent {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid user_id 
  varchar secondary_phone_number 
  varchar occupation 
  varchar work_address 
  text relationship_notes 
  varchar emergency_contact_name 
  varchar emergency_contact_phone 
  boolean is_active 
}
Student {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid branch_id 
  varchar first_name 
  varchar last_name 
  varchar gender 
  date date_of_birth 
  varchar roll_no 
  uuid current_section_id 
  date admission_date 
  uuid photo_id 
  varchar status 
}
StudentAcademicYearSection {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid student_id 
  uuid academic_year_id 
  uuid section_id 
}
ParentStudentLink {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid student_id 
  uuid parent_id 
  varchar relationship_type 
  boolean is_primary_contact 
}
Teacher {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid user_id 
  uuid organization_id 
  uuid branch_id 
  varchar employee_id 
  text bio 
  varchar specialization 
  date joining_date 
}
TeacherQualification {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid teacher_id 
  uuid organization_id 
  varchar degree_name 
  varchar institution 
  varchar field_of_study 
  date completion_date 
  uuid certificate_copy_id 
}
TeacherSubjectAssignment {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid teacher_id 
  uuid organization_id 
  uuid subject_id 
  uuid section_id 
  uuid academic_year_id 
}
HomeroomAssignment {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid branch_id 
  uuid academic_year_id 
  uuid section_id 
  uuid teacher_id 
  text notes 
}
Attendance {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid branch_id 
  uuid academic_year_id 
  uuid section_id 
  uuid student_id 
  uuid recorded_by_id 
  date date 
  varchar status 
  text remarks 
  uuid client_side_id 
}
AttendanceReason {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid attendance_id 
  varchar reason_category 
  text note 
  boolean parent_confirmed 
  uuid confirmed_by_id 
  timestamp_with_time_zone confirmed_at 
}
AttendanceSummary {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid student_id 
  uuid academic_year_id 
  integer total_present 
  integer total_absent 
  integer total_late 
  integer total_excused 
  integer total_school_days 
  timestamp_with_time_zone last_updated 
}
Assessment {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid branch_id 
  uuid teacher_assignment_id 
  varchar title 
  varchar task_type 
  text description 
  numeric total_marks 
  numeric passing_marks 
  date due_date 
  varchar status 
}
AssessmentResult {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid assessment_id 
  uuid student_id 
  uuid graded_by_id 
  numeric obtained_marks 
  varchar submission_status 
  text feedback 
  boolean parent_confirmed 
  uuid parent_confirmed_by_id 
  timestamp_with_time_zone parent_confirmed_at 
}
HomeworkConfirmation {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid branch_id 
  uuid section_id 
  uuid assessment_id 
  uuid student_id 
  boolean is_confirmed 
  timestamp_with_time_zone confirmed_at 
  text feedback 
  uuid confirmed_by_id 
}
Announcement {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid organization_id 
  uuid branch_id 
  varchar subject 
  text message 
  uuid attachment_id 
  timestamp_with_time_zone scheduled_at 
  boolean is_urgent 
  varchar status 
  varchar target_roles 
}
AnnouncementGrade {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid announcement_id 
  uuid grade_id 
}
AnnouncementSection {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid announcement_id 
  uuid section_id 
}
ChatThread {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid parent_id 
  uuid teacher_id 
  uuid student_id 
  uuid organization_id 
  uuid branch_id 
}
ChatMessage {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid thread_id 
  uuid sender_id 
  text text 
  uuid attachment_id 
}
MessageRead {
  uuid id pk
  timestamp_with_time_zone created_at 
  timestamp_with_time_zone updated_at 
  uuid message_id 
  uuid reader_id 
  timestamp_with_time_zone read_at 
}
ApprovalLoginToken }|--|| User: ""
ParentLoginOTP }|--|| User: ""
AcademicYear }|--|| Organization: ""
AcademicYear }|--|| Branch: ""
AnnouncementGrade }|--|| Announcement: ""
AnnouncementGrade }|--|| Grade: ""
AnnouncementSection }|--|| Announcement: ""
AnnouncementSection }|--|| Section: ""
Grade }|--|| Organization: ""
Grade }|--|| Branch: ""
MessageRead }|--|| ChatMessage: ""
MessageRead }|--|| User: ""
ParentStudentLink }|--|| Student: ""
ParentStudentLink }|--|| Parent: ""
School }|--|| Organization: ""
School }|--|| MediaFile: ""
Announcement }|--|| Organization: ""
Announcement }|--|| Branch: ""
Announcement }|--|| MediaFile: ""
Assessment }|--|| Organization: ""
Assessment }|--|| Branch: ""
Assessment }|--|| TeacherSubjectAssignment: ""
AttendanceReason }|--|| Organization: ""
AttendanceReason ||--|| Attendance: ""
AttendanceReason }|--|| User: ""
AttendanceSummary }|--|| Organization: ""
AttendanceSummary }|--|| Student: ""
AttendanceSummary }|--|| AcademicYear: ""
Branch }|--|{ Parent: ""
Branch }|--|| Organization: ""
Branch }|--|| School: ""
BranchAdmin }|--|| Organization: ""
BranchAdmin }|--|| Branch: ""
BranchAdmin }|--|| User: ""
ChatMessage }|--|| ChatThread: ""
ChatMessage }|--|| User: ""
ChatMessage }|--|| MediaFile: ""
GradeSubject }|--|| Organization: ""
GradeSubject }|--|| Grade: ""
GradeSubject }|--|| Subject: ""
Organization }|--|{ Parent: ""
Organization }|--|| User: ""
Organization }|--|| MediaFile: ""
Parent ||--|| User: ""
StudentAcademicYearSection }|--|| Student: ""
StudentAcademicYearSection }|--|| AcademicYear: ""
StudentAcademicYearSection }|--|| Section: ""
Subject }|--|| Organization: ""
Subject }|--|| Branch: ""
Subject }|--|| Grade: ""
Teacher ||--|| User: ""
Teacher }|--|| Organization: ""
Teacher }|--|| Branch: ""
TeacherQualification }|--|| Teacher: ""
TeacherQualification }|--|| Organization: ""
TeacherQualification }|--|| MediaFile: ""
CalendarDocument }|--|| Organization: ""
CalendarDocument }|--|| Branch: ""
CalendarDocument }|--|| AcademicYear: ""
CalendarDocument }|--|| MediaFile: ""
Section }|--|| Organization: ""
Section }|--|| Branch: ""
Section }|--|| Grade: ""
Section }|--|| AcademicYear: ""
Student }|--|| Organization: ""
Student }|--|| Branch: ""
Student }|--|| Section: ""
Student }|--|| MediaFile: ""
AssessmentResult }|--|| Organization: ""
AssessmentResult }|--|| Assessment: ""
AssessmentResult }|--|| Student: ""
AssessmentResult }|--|| User: ""
ChatThread }|--|| Parent: ""
ChatThread }|--|| Teacher: ""
ChatThread }|--|| Student: ""
ChatThread }|--|| Organization: ""
ChatThread }|--|| Branch: ""
HomeroomAssignment }|--|| Organization: ""
HomeroomAssignment }|--|| Branch: ""
HomeroomAssignment }|--|| AcademicYear: ""
HomeroomAssignment }|--|| Section: ""
HomeroomAssignment }|--|| Teacher: ""
TeacherSubjectAssignment }|--|| Teacher: ""
TeacherSubjectAssignment }|--|| Organization: ""
TeacherSubjectAssignment }|--|| Subject: ""
TeacherSubjectAssignment }|--|| Section: ""
TeacherSubjectAssignment }|--|| AcademicYear: ""
User ||--|| Token: ""
User }|--|{ Group: ""
User }|--|{ Permission: ""
HomeworkConfirmation }|--|| Organization: ""
HomeworkConfirmation }|--|| Branch: ""
HomeworkConfirmation }|--|| Section: ""
HomeworkConfirmation }|--|| Assessment: ""
HomeworkConfirmation }|--|| Student: ""
HomeworkConfirmation }|--|| User: ""
Attendance }|--|| Organization: ""
Attendance }|--|| Branch: ""
Attendance }|--|| AcademicYear: ""
Attendance }|--|| Section: ""
Attendance }|--|| Student: ""
Attendance }|--|| User: ""