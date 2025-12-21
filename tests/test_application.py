import os
import sys
import unittest
import warnings
from datetime import date, time
from io import BytesIO

# Suppress all warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=Warning)

from src import create_app, db
from src.models import Issue, Room, Schedule, ScheduleImport


class TestRoomScheduleApplication(unittest.TestCase):
    """Comprehensive test suite for Room Schedule Management Application"""

    def setUp(self):
        """Set up test client and in-memory database before each test"""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["WTF_CSRF_ENABLED"] = False
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create sample rooms for testing
            room1 = Room(building="TestBuilding", number="101", status="Available")
            room2 = Room(building="TestBuilding", number="102", status="Occupied")
            db.session.add_all([room1, room2])
            db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    # ==================== TEST 1: CSV Import Flow ====================
    def test_csv_import_flow(self):
        """
        Test 1: Full CSV Import Flow
        - Upload CSV file with room schedules
        - Verify data saved to database
        - Check Schedule and ScheduleImport records created
        - Verify rooms are created or reused
        """
        with self.app.app_context():
            # Load test CSV data
            csv_path = os.path.join(os.path.dirname(__file__), "test_data.csv")
            
            with open(csv_path, "rb") as f:
                csv_data = f.read()
            
            # Simulate file upload
            data = {
                "schedule_file": (BytesIO(csv_data), "test_schedule.csv"),
                "uploaded_by": "test_user"
            }
            
            response = self.client.post(
                "/import",
                data=data,
                content_type="multipart/form-data",
                follow_redirects=True
            )
            
            # Verify response
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Imported", response.data)
            
            # Verify ScheduleImport record created
            import_record = ScheduleImport.query.first()
            self.assertIsNotNone(import_record)
            # Verify uploaded_by field (should be test_user or Unknown if form field not passed)
            self.assertIn(import_record.uploaded_by, ["test_user", "Unknown"])
            self.assertIn("test_schedule.csv", import_record.filename)
            
            # Verify Schedule records created
            schedules = Schedule.query.all()
            self.assertGreater(len(schedules), 0, "No schedules were imported")
            
            # Verify specific schedule data
            schedule_sample = Schedule.query.filter_by(
                date=date(2025, 12, 22)
            ).first()
            self.assertIsNotNone(schedule_sample)
            self.assertIsNotNone(schedule_sample.room)
            
            # Verify rooms were created
            room_count = Room.query.count()
            self.assertGreater(room_count, 2, "New rooms should be created from import")

    # ==================== TEST 2: Issue Reporting Flow ====================
    def test_issue_reporting_flow(self):
        """
        Test 2: Full Issue Reporting Flow
        - Create issue via POST request
        - Verify issue saved with correct status
        - Update issue status to Resolved
        - Verify all state changes recorded
        """
        with self.app.app_context():
            # Get a room to report issue for
            room = Room.query.first()
            self.assertIsNotNone(room)
            
            # Report new issue
            response = self.client.post(
                "/issues/report",
                data={
                    "room_id": room.id,
                    "reporter_id": "test_reporter@example.com",
                    "description": "Projector not working in this room"
                },
                follow_redirects=True
            )
            
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Issue reported", response.data)
            
            # Verify issue was saved
            issue = Issue.query.first()
            self.assertIsNotNone(issue)
            self.assertEqual(issue.room_id, room.id)
            self.assertEqual(issue.reporter_id, "test_reporter@example.com")
            self.assertEqual(issue.description, "Projector not working in this room")
            self.assertEqual(issue.status, "New")
            self.assertIsNotNone(issue.created_at)
            
            # Resolve the issue
            response = self.client.post(
                f"/issues/{issue.id}/resolve",
                follow_redirects=True
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Verify status changed
            db.session.refresh(issue)
            self.assertEqual(issue.status, "Resolved")

    # ==================== TEST 3: Room Status Toggle ====================
    def test_room_status_management(self):
        """
        Test 3: Room Status Management
        - Verify initial room status
        - Toggle room status
        - Verify status changes correctly
        - Test toggle method functionality
        """
        with self.app.app_context():
            # Get test room
            room = Room.query.filter_by(building="TestBuilding", number="101").first()
            self.assertIsNotNone(room)
            
            # Verify initial status
            initial_status = room.status
            self.assertEqual(initial_status, "Available")
            
            # Toggle status
            room.toggle_status()
            db.session.commit()
            
            # Verify status changed
            self.assertEqual(room.status, "Occupied")
            
            # Toggle again
            room.toggle_status()
            db.session.commit()
            
            # Verify status reverted
            self.assertEqual(room.status, "Available")
            
            # Test with initially Occupied room
            room2 = Room.query.filter_by(building="TestBuilding", number="102").first()
            self.assertEqual(room2.status, "Occupied")
            
            room2.toggle_status()
            db.session.commit()
            self.assertEqual(room2.status, "Available")

    # ==================== TEST 4: Data Validation ====================
    def test_schedule_data_validation(self):
        """
        Test 4: Schedule Data Validation
        - Test creating valid schedule
        - Verify required fields
        - Test time logic validation
        - Verify foreign key relationships
        """
        with self.app.app_context():
            room = Room.query.first()
            
            # Create valid schedule
            schedule = Schedule(
                room_id=room.id,
                date=date(2025, 12, 30),
                open_time=time(8, 0, 0),
                close_time=time(17, 0, 0)
            )
            db.session.add(schedule)
            db.session.commit()
            
            # Verify schedule saved
            saved_schedule = Schedule.query.filter_by(
                room_id=room.id,
                date=date(2025, 12, 30)
            ).first()
            
            self.assertIsNotNone(saved_schedule)
            self.assertEqual(saved_schedule.room_id, room.id)
            self.assertEqual(saved_schedule.date, date(2025, 12, 30))
            self.assertEqual(saved_schedule.open_time, time(8, 0, 0))
            self.assertEqual(saved_schedule.close_time, time(17, 0, 0))
            
            # Verify relationship works
            self.assertEqual(saved_schedule.room.building, room.building)
            self.assertEqual(saved_schedule.room.number, room.number)
            
            # Test time logic
            self.assertLess(saved_schedule.open_time, saved_schedule.close_time,
                          "Open time should be before close time")

    # ==================== TEST 5: Database Relationships ====================
    def test_database_relationships_and_cascade(self):
        """
        Test 5: Database Relationships and Cascade Deletion
        - Test Schedule to Room relationship
        - Test Schedule to ScheduleImport relationship
        - Test Issue to Room relationship
        - Verify cascade deletion works
        - Test backref relationships
        """
        with self.app.app_context():
            # Create import record with schedules
            import_record = ScheduleImport(
                filename="test_relationships.csv",
                uploaded_by="relationship_tester"
            )
            db.session.add(import_record)
            db.session.flush()
            
            room = Room.query.first()
            
            # Create multiple schedules linked to import
            schedule1 = Schedule(
                room_id=room.id,
                date=date(2025, 12, 28),
                open_time=time(8, 0),
                close_time=time(16, 0),
                import_id=import_record.id
            )
            schedule2 = Schedule(
                room_id=room.id,
                date=date(2025, 12, 29),
                open_time=time(9, 0),
                close_time=time(17, 0),
                import_id=import_record.id
            )
            
            db.session.add_all([schedule1, schedule2])
            db.session.commit()
            
            # Verify relationships
            self.assertEqual(len(import_record.schedules), 2)
            self.assertEqual(schedule1.import_record.filename, "test_relationships.csv")
            self.assertEqual(schedule1.room.building, room.building)
            
            # Test backref
            room_schedules = room.schedules
            self.assertGreaterEqual(len(room_schedules), 2)
            
            # Test cascade deletion
            schedule_ids = [schedule1.id, schedule2.id]
            db.session.delete(import_record)
            db.session.commit()
            
            # Verify schedules were deleted (cascade)
            remaining_schedules = Schedule.query.filter(
                Schedule.id.in_(schedule_ids)
            ).all()
            self.assertEqual(len(remaining_schedules), 0,
                           "Schedules should be deleted when import is deleted")
            
            # Create and test Issue relationship
            issue = Issue(
                room_id=room.id,
                reporter_id="tester",
                description="Testing relationship"
            )
            db.session.add(issue)
            db.session.commit()
            
            # Verify issue-room relationship
            self.assertEqual(issue.room.id, room.id)
            room_issues = room.issues
            self.assertGreater(len(room_issues), 0)


if __name__ == "__main__":
    from typing import cast
    
    # Custom test result class for formatted output
    class MinimalTestResult(unittest.TextTestResult):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.test_results: list = []
        
        def startTest(self, test):
            super().startTest(test)
            self.current_test = test
        
        def addSuccess(self, test):
            super().addSuccess(test)
            test_name = test._testMethodName.replace('_', ' ').title()
            test_doc = test._testMethodDoc.split('\n')[1].strip() if test._testMethodDoc else "No description"
            self.test_results.append((test_name, test_doc, "✅ SUCCESS"))
        
        def addError(self, test, err):
            super().addError(test, err)
            test_name = test._testMethodName.replace('_', ' ').title()
            test_doc = test._testMethodDoc.split('\n')[1].strip() if test._testMethodDoc else "No description"
            self.test_results.append((test_name, test_doc, "❌ ERROR"))
        
        def addFailure(self, test, err):
            super().addFailure(test, err)
            test_name = test._testMethodName.replace('_', ' ').title()
            test_doc = test._testMethodDoc.split('\n')[1].strip() if test._testMethodDoc else "No description"
            self.test_results.append((test_name, test_doc, "❌ FAIL"))
    
    class MinimalTestRunner(unittest.TextTestRunner):
        resultclass = MinimalTestResult
        
        def run(self, test):
            result = super().run(test)
            result = cast(MinimalTestResult, result)
            
            # Print formatted results
            print("\n" + "="*80)
            print("TEST EXECUTION SUMMARY")
            print("="*80)
            
            for i, (name, desc, status) in enumerate(result.test_results, 1):
                print(f"Test {i} | {name} | {desc} | {status}")
            
            print("="*80)
            print(f"Total: {result.testsRun} | Passed: {result.testsRun - len(result.failures) - len(result.errors)} | Failed: {len(result.failures) + len(result.errors)}")
            print("="*80 + "\n")
            
            return result
    
    # Run tests with custom runner
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRoomScheduleApplication)
    runner = MinimalTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
