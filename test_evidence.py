
from modules.evidence_manager import save_evidence, get_evidence_path


class TestVideo:
    name = "test_video.mp4"

    def getbuffer(self):
        return b"This is sample video evidence."


try:
    # Save test evidence
    saved_path = save_evidence(TestVideo())
    print("Evidence saved successfully!")
    print("Saved location:", saved_path)

    # Check saved file
    full_path = get_evidence_path(saved_path)

    if full_path:
        print("File exists:", full_path.exists())
        print("Evidence storage test PASSED!")
    else:
        print("Evidence file not found.")

except Exception as error:
    print("Test failed:", error)
