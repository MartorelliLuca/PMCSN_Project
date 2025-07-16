from interfaces.RandomSampler import RandomSampler

class StaticSampler(RandomSampler):
    def sample(self) -> float:
        return 0.42
