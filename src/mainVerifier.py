import desPython.rng as rng
import desPython.rngs as rngs
import desPython.rvms as rvms

class MainVerifier:
    def __init__(self):
        self.results = {}

    def test_rng(self):
        try:
            rng.testRandom()
            numeroRandom1 = rng.random()
            print(f"🔢 Valore casuale da rng: {numeroRandom1:.4f}")
            self.results["rng"] = "✅ Passed"
        except Exception as e:
            self.results["rng"] = f"❌ Failed: {e}"

    def test_rngs(self):
        try:
            rngs.testRandom()
            numeroRandom2 = rngs.random()
            print(f"🔢 Valore casuale da rngs: {numeroRandom2:.4f}")
            self.results["rngs"] = "✅ Passed"
        except Exception as e:
            self.results["rngs"] = f"❌ Failed: {e}"

    def test_rvms(self):
        try:
            value = rvms.idfNormal(0, 1, 0.975)
            if 1.9 < value < 2.1:
                self.results["rvms"] = f"✅ Passed (idfNormal(0,1,0.975) ≈ {value:.4f})"
            else:
                self.results["rvms"] = f"⚠️ Unexpected value: {value}"
        except Exception as e:
            self.results["rvms"] = f"❌ Failed: {e}"

    def run_all_tests(self):
        print("🔍 Avvio test sulle librerie...\n")
        self.test_rng()
        self.test_rngs()
        self.test_rvms()

        print("\n📊 Risultati:")
        for mod, outcome in self.results.items():
            print(f"  - {mod}: {outcome}")


if __name__ == "__main__":
    verifier = MainVerifier()
    verifier.run_all_tests()
