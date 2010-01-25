class Set():
	distance = None
	TrafficULvictim = None
	TrafficULintefering = None

	def __init__(self, distance = 0, TrafficULvictim = 0, TrafficULintefering = 0):
		self.distance = distance
		self.TrafficULvictim = TrafficULvictim
		self.TrafficULintefering = TrafficULintefering

params = Set()

params.distance = 100
params.TrafficULvictim = 2E6
params.TrafficULintefering = 0 #2E6

