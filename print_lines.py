"""Scratch file for inspecting generated line numbers during local debugging."""

SCRIPT_LINES = [
    "def run_no_catch(self):",
    "    from django.db import transaction",
    "    import pandas as pd",
    "    import io",
    "",
    "    data = io.StringIO(self.file_content.decode('utf-8'))",
    "    df = pd.read_csv(data)",
    "    df.columns = [str(c).strip().lower() for c in df.columns]",
    "    df = df.fillna('')",
    "",
    "    seen_roll_numbers = set()",
    "    org = Organization.objects.get(id=self.organization_id)",
    "    branch = Branch.objects.get(id=self.branch_id, organization=org)",
    "",
    "    for index, row in df.iterrows():",
    "        row_num = index + 2",
    "        row_errors = {}",
    "",
    (
        "        first_name = str(row.get('first_name')).strip() if "
        "row.get('first_name') is not None else ''"
    ),
    (
        "        last_name = str(row.get('last_name')).strip() if "
        "row.get('last_name') is not None else ''"
    ),
    (
        "        gender_raw = str(row.get('gender')).strip().upper() if "
        "row.get('gender') is not None else ''"
    ),
    "        date_of_birth_raw = row.get('date_of_birth')",
    (
        "        roll_no = str(row.get('roll_no')).strip() if "
        "row.get('roll_no') is not None else ''"
    ),
]

script = "\n".join(SCRIPT_LINES)
LINE_NUMBERS = [f"{index:2d}: {line}" for index, line in enumerate(SCRIPT_LINES, 1)]
