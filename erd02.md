Table User {
  id "uuid" [primary key]
  password "varchar" 
  last_login "timestamp with time zone" 
  is_superuser "boolean" 
  first_name "varchar" 
  last_name "varchar" 
  is_staff "boolean" 
  is_active "boolean" 
  date_joined "timestamp with time zone" 
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  email "varchar" 
  name "varchar" 
  father_name "varchar" 
  grandfather_name "varchar" 
  role "varchar" 
  phone_number "varchar" 
  address "varchar" 
  verified_at "timestamp with time zone" 
}
Table ApprovalLoginToken {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  user_id "uuid" 
  token_hash "varchar" 
  expires_at "timestamp with time zone" 
  used_at "timestamp with time zone" 
}
Table ParentLoginOTP {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  user_id "uuid" 
  phone_number "varchar" 
  code_hash "varchar" 
  expires_at "timestamp with time zone" 
  used_at "timestamp with time zone" 
  failed_attempts "smallint" 
}
Table Organization {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  owner_id "uuid" 
  name "varchar" 
  trade_name "varchar" 
  tin_number "varchar" 
  license_no "varchar" 
  client_full_name "varchar" 
  business_address "text" 
  business_phone_number "varchar" 
  client_phone_number "varchar" 
  business_license_image_id "uuid" 
  status "varchar" 
  verification_status "varchar" 
  verification_checked_at "timestamp with time zone" 
  verification_failure_reason "varchar" 
  verification_match_source "varchar" 
  verified_name "varchar" 
  verified_license_no "varchar" 
  verified_tin_number "varchar" 
}
Table School {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  name "varchar" 
  description "text" 
  country "varchar" 
  contact_email "varchar" 
  contact_phone "varchar" 
  logo_id "uuid" 
  website "varchar" 
  status "varchar" 
}
Table Branch {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  school_id "uuid" 
  name "varchar" 
  address "text" 
  city "varchar" 
  region "varchar" 
  contact_phone "varchar" 
  contact_email "varchar" 
  status "varchar" 
}
Table BranchAdmin {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  branch_id "uuid" 
  user_id "uuid" 
  emergency_contact_name "varchar" 
  emergency_contact_phone "varchar" 
  role_title "varchar" 
  qualification "varchar" 
  status "varchar" 
  last_login "timestamp with time zone" 
}
Table AcademicYear {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  branch_id "uuid" 
  name "varchar" 
  start_date "date" 
  end_date "date" 
  is_current "boolean" 
}
Table Grade {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  branch_id "uuid" 
  name "varchar" 
  level "integer" 
}
Table Section {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  branch_id "uuid" 
  grade_id "uuid" 
  academic_year_id "uuid" 
  name "varchar" 
}
Table Subject {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  branch_id "uuid" 
  grade_id "uuid" 
  name "varchar" 
  code "varchar" 
}
Table GradeSubject {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  grade_id "uuid" 
  subject_id "uuid" 
}
Table CalendarDocument {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  branch_id "uuid" 
  academic_year_id "uuid" 
  media_file_id "uuid" 
}
Table Parent {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  user_id "uuid" 
  secondary_phone_number "varchar" 
  occupation "varchar" 
  work_address "varchar" 
  relationship_notes "text" 
  emergency_contact_name "varchar" 
  emergency_contact_phone "varchar" 
  is_active "boolean" 
}
Table Student {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  branch_id "uuid" 
  first_name "varchar" 
  last_name "varchar" 
  gender "varchar" 
  date_of_birth "date" 
  roll_no "varchar" 
  current_section_id "uuid" 
  admission_date "date" 
  photo_id "uuid" 
  status "varchar" 
}
Table StudentAcademicYearSection {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  student_id "uuid" 
  academic_year_id "uuid" 
  section_id "uuid" 
}
Table ParentStudentLink {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  student_id "uuid" 
  parent_id "uuid" 
  relationship_type "varchar" 
  is_primary_contact "boolean" 
}
Table Teacher {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  user_id "uuid" 
  organization_id "uuid" 
  branch_id "uuid" 
  employee_id "varchar" 
  bio "text" 
  specialization "varchar" 
  joining_date "date" 
}
Table TeacherQualification {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  teacher_id "uuid" 
  organization_id "uuid" 
  degree_name "varchar" 
  institution "varchar" 
  field_of_study "varchar" 
  completion_date "date" 
  certificate_copy_id "uuid" 
}
Table TeacherSubjectAssignment {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  teacher_id "uuid" 
  organization_id "uuid" 
  subject_id "uuid" 
  section_id "uuid" 
  academic_year_id "uuid" 
}
Table HomeroomAssignment {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  branch_id "uuid" 
  academic_year_id "uuid" 
  section_id "uuid" 
  teacher_id "uuid" 
  notes "text" 
}
Table Attendance {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  branch_id "uuid" 
  academic_year_id "uuid" 
  section_id "uuid" 
  student_id "uuid" 
  recorded_by_id "uuid" 
  date "date" 
  status "varchar" 
  remarks "text" 
  client_side_id "uuid" 
}
Table AttendanceReason {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  attendance_id "uuid" 
  reason_category "varchar" 
  note "text" 
  parent_confirmed "boolean" 
  confirmed_by_id "uuid" 
  confirmed_at "timestamp with time zone" 
}
Table AttendanceSummary {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  student_id "uuid" 
  academic_year_id "uuid" 
  total_present "integer" 
  total_absent "integer" 
  total_late "integer" 
  total_excused "integer" 
  total_school_days "integer" 
  last_updated "timestamp with time zone" 
}
Table Assessment {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  branch_id "uuid" 
  teacher_assignment_id "uuid" 
  title "varchar" 
  task_type "varchar" 
  description "text" 
  total_marks "numeric" 
  passing_marks "numeric" 
  due_date "date" 
  status "varchar" 
}
Table AssessmentResult {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  assessment_id "uuid" 
  student_id "uuid" 
  graded_by_id "uuid" 
  obtained_marks "numeric" 
  submission_status "varchar" 
  feedback "text" 
  parent_confirmed "boolean" 
  parent_confirmed_by_id "uuid" 
  parent_confirmed_at "timestamp with time zone" 
}
Table HomeworkConfirmation {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  branch_id "uuid" 
  section_id "uuid" 
  assessment_id "uuid" 
  student_id "uuid" 
  is_confirmed "boolean" 
  confirmed_at "timestamp with time zone" 
  feedback "text" 
  confirmed_by_id "uuid" 
}
Table Announcement {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  organization_id "uuid" 
  branch_id "uuid" 
  subject "varchar" 
  message "text" 
  attachment_id "uuid" 
  scheduled_at "timestamp with time zone" 
  is_urgent "boolean" 
  status "varchar" 
  target_roles "varchar" 
}
Table AnnouncementGrade {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  announcement_id "uuid" 
  grade_id "uuid" 
}
Table AnnouncementSection {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  announcement_id "uuid" 
  section_id "uuid" 
}
Table ImportJob {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  status "varchar" 
  task_id "varchar" 
  file_id "uuid" 
  module "varchar" 
  organization_id "uuid" 
  branch_id "uuid" 
  current_section_id "uuid" 
  errors "jsonb" 
  progress "integer" 
  created_by_id "uuid" 
}
Table ChatThread {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  parent_id "uuid" 
  teacher_id "uuid" 
  student_id "uuid" 
  organization_id "uuid" 
  branch_id "uuid" 
}
Table ChatMessage {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  thread_id "uuid" 
  sender_id "uuid" 
  text "text" 
  attachment_id "uuid" 
}
Table MessageRead {
  id "uuid" [primary key]
  created_at "timestamp with time zone" 
  updated_at "timestamp with time zone" 
  message_id "uuid" 
  reader_id "uuid" 
  read_at "timestamp with time zone" 
}
Ref: ApprovalLoginToken.user_id > User.id
Ref: ParentLoginOTP.user_id > User.id
Ref: AcademicYear.organization_id > Organization.id
Ref: AcademicYear.branch_id > Branch.id
Ref: AnnouncementGrade.announcement_id > Announcement.id
Ref: AnnouncementGrade.grade_id > Grade.id
Ref: AnnouncementSection.announcement_id > Announcement.id
Ref: AnnouncementSection.section_id > Section.id
Ref: Grade.organization_id > Organization.id
Ref: Grade.branch_id > Branch.id
Ref: MessageRead.message_id > ChatMessage.id
Ref: MessageRead.reader_id > User.id
Ref: ParentStudentLink.student_id > Student.id
Ref: ParentStudentLink.parent_id > Parent.id
Ref: School.organization_id > Organization.id
Ref: School.logo_id > MediaFile.id
Ref: Announcement.organization_id > Organization.id
Ref: Announcement.branch_id > Branch.id
Ref: Announcement.attachment_id > MediaFile.id
Ref: Assessment.organization_id > Organization.id
Ref: Assessment.branch_id > Branch.id
Ref: Assessment.teacher_assignment_id > TeacherSubjectAssignment.id
Ref: AttendanceReason.organization_id > Organization.id
Ref: AttendanceReason.id - Attendance.id
Ref: AttendanceReason.confirmed_by_id > User.id
Ref: AttendanceSummary.organization_id > Organization.id
Ref: AttendanceSummary.student_id > Student.id
Ref: AttendanceSummary.academic_year_id > AcademicYear.id
Ref: Branch.id <> Parent.id
Ref: Branch.organization_id > Organization.id
Ref: Branch.school_id > School.id
Ref: BranchAdmin.organization_id > Organization.id
Ref: BranchAdmin.branch_id > Branch.id
Ref: BranchAdmin.user_id > User.id
Ref: ChatMessage.thread_id > ChatThread.id
Ref: ChatMessage.sender_id > User.id
Ref: ChatMessage.attachment_id > MediaFile.id
Ref: GradeSubject.organization_id > Organization.id
Ref: GradeSubject.grade_id > Grade.id
Ref: GradeSubject.subject_id > Subject.id
Ref: Organization.id <> Parent.id
Ref: Organization.owner_id > User.id
Ref: Organization.business_license_image_id > MediaFile.id
Ref: Parent.id - User.id
Ref: StudentAcademicYearSection.student_id > Student.id
Ref: StudentAcademicYearSection.academic_year_id > AcademicYear.id
Ref: StudentAcademicYearSection.section_id > Section.id
Ref: Subject.organization_id > Organization.id
Ref: Subject.branch_id > Branch.id
Ref: Subject.grade_id > Grade.id
Ref: Teacher.id - User.id
Ref: Teacher.organization_id > Organization.id
Ref: Teacher.branch_id > Branch.id
Ref: TeacherQualification.teacher_id > Teacher.id
Ref: TeacherQualification.organization_id > Organization.id
Ref: TeacherQualification.certificate_copy_id > MediaFile.id
Ref: CalendarDocument.organization_id > Organization.id
Ref: CalendarDocument.branch_id > Branch.id
Ref: CalendarDocument.academic_year_id > AcademicYear.id
Ref: CalendarDocument.media_file_id > MediaFile.id
Ref: Section.organization_id > Organization.id
Ref: Section.branch_id > Branch.id
Ref: Section.grade_id > Grade.id
Ref: Section.academic_year_id > AcademicYear.id
Ref: Student.organization_id > Organization.id
Ref: Student.branch_id > Branch.id
Ref: Student.current_section_id > Section.id
Ref: Student.photo_id > MediaFile.id
Ref: AssessmentResult.organization_id > Organization.id
Ref: AssessmentResult.assessment_id > Assessment.id
Ref: AssessmentResult.student_id > Student.id
Ref: AssessmentResult.graded_by_id > User.id
Ref: AssessmentResult.parent_confirmed_by_id > User.id
Ref: ChatThread.parent_id > Parent.id
Ref: ChatThread.teacher_id > Teacher.id
Ref: ChatThread.student_id > Student.id
Ref: ChatThread.organization_id > Organization.id
Ref: ChatThread.branch_id > Branch.id
Ref: HomeroomAssignment.organization_id > Organization.id
Ref: HomeroomAssignment.branch_id > Branch.id
Ref: HomeroomAssignment.academic_year_id > AcademicYear.id
Ref: HomeroomAssignment.section_id > Section.id
Ref: HomeroomAssignment.teacher_id > Teacher.id
Ref: ImportJob.file_id > MediaFile.id
Ref: ImportJob.organization_id > Organization.id
Ref: ImportJob.branch_id > Branch.id
Ref: ImportJob.current_section_id > Section.id
Ref: ImportJob.created_by_id > User.id
Ref: TeacherSubjectAssignment.teacher_id > Teacher.id
Ref: TeacherSubjectAssignment.organization_id > Organization.id
Ref: TeacherSubjectAssignment.subject_id > Subject.id
Ref: TeacherSubjectAssignment.section_id > Section.id
Ref: TeacherSubjectAssignment.academic_year_id > AcademicYear.id
Ref: User.id - Token.key
Ref: User.id <> Group.id
Ref: User.id <> Permission.id
Ref: HomeworkConfirmation.organization_id > Organization.id
Ref: HomeworkConfirmation.branch_id > Branch.id
Ref: HomeworkConfirmation.section_id > Section.id
Ref: HomeworkConfirmation.assessment_id > Assessment.id
Ref: HomeworkConfirmation.student_id > Student.id
Ref: HomeworkConfirmation.confirmed_by_id > User.id
Ref: Attendance.organization_id > Organization.id
Ref: Attendance.branch_id > Branch.id
Ref: Attendance.academic_year_id > AcademicYear.id
Ref: Attendance.section_id > Section.id
Ref: Attendance.student_id > Student.id
Ref: Attendance.recorded_by_id > User.id