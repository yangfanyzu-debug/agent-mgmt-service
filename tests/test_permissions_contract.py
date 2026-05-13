import unittest

from app.services.permissions import OwnershipError, add_can_edit, ensure_can_edit


class PermissionContractTests(unittest.TestCase):
    def test_add_can_edit_marks_only_records_created_by_current_user_editable(self):
        rows = [
            {"id": 1, "agent_name": "own_agent", "created_by_user_id": 7},
            {"id": 2, "agent_name": "other_agent", "created_by_user_id": 8},
        ]

        enriched = add_can_edit(rows, current_user_id=7)

        self.assertIs(enriched[0]["can_edit"], True)
        self.assertIs(enriched[1]["can_edit"], False)

    def test_ensure_can_edit_allows_owner_and_rejects_non_owner(self):
        own = {"id": 1, "created_by_user_id": 7}
        other = {"id": 2, "created_by_user_id": 8}

        ensure_can_edit(own, current_user_id=7)

        with self.assertRaises(OwnershipError):
            ensure_can_edit(other, current_user_id=7)


if __name__ == "__main__":
    unittest.main()
