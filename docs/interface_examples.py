from __future__ import unicode_literals
from __future__ import print_function
from detector.interface import IDetector

class MyDetector( object ):
    exposure = 0.1
    def acquire( self, exposure, nframes=1, dac=42 ):
        print("Acquiring...")

# Register MyDetector to as implementing the IDetector interface
IDetector.register( MyDetector )

# Verify the implementation of the IDetector interface in MyDetector
print("MyDetector provides IDetector: ", issubclass( MyDetector, IDetector ))        

# Create an instance of MyDetector
det = MyDetector()

# Verify that the det object implements the IDetector interface
print("det implements IDetector: ", isinstance( det, IDetector ))
