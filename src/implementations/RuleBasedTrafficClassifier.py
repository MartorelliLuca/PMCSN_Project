from interfaces.TrafficClassifier import TrafficClassifier

class RuleBasedTrafficClassifier(TrafficClassifier):
    def classify(self, packet: dict) -> str:
        if packet.get("size", 0) > 1000:
            return "ddos"
        elif packet.get("sospetto", False):
            return "suspicious"
        return "normal"