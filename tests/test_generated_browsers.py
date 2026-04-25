import random
import string

import pytest

from is_crawler import is_crawler

_WINDOWS = (
    "Windows NT 5.1",
    "Windows NT 6.1",
    "Windows NT 6.2",
    "Windows NT 6.3",
    "Windows NT 10.0",
    "Windows NT 11.0",
)
_LINUX_CPU = ("i686", "x86_64")
_MAC_CPU = ("Intel", "U; Intel", "U; PPC")
_ANDROID = ("8.0.0", "9", "10", "11", "12", "13", "14", "15")
_IOS = ("14.8.1", "15.8.2", "16.7.7", "17.4.1", "17.5", "18.0", "18.5")
_APPLE = ("iPhone", "iPad")
_LOCALES = ("en-US", "de-DE", "fr-FR", "ja-JP", "zh-CN", "es-ES", "pt-BR")


class UA:
    def __init__(self, seed: int) -> None:
        self.r = random.Random(seed)

    def pick(self, seq):
        return self.r.choice(seq)

    def win(self) -> str:
        return self.pick(_WINDOWS)

    def linux(self) -> str:
        return f"X11; Linux {self.pick(_LINUX_CPU)}"

    def mac(self) -> str:
        return f"Macintosh; {self.pick(_MAC_CPU)} Mac OS X 10_{self.r.randint(5, 15)}_{self.r.randint(0, 9)}"

    def android(self) -> str:
        return f"Android {self.pick(_ANDROID)}"

    def ios(self) -> str:
        dev = self.pick(_APPLE)
        return f"{dev}; CPU {dev} OS {self.pick(_IOS).replace('.', '_')} like Mac OS X"

    def chrome(self) -> str:
        saf = f"{self.r.randint(531, 537)}.{self.r.randint(0, 36)}"
        ver = self.r.randint(80, 137)
        bld = self.r.randint(1000, 6000)
        plat = self.pick(
            (
                self.linux(),
                self.win(),
                self.mac(),
                f"Linux; {self.android()}",
            )
        )
        mobile = " Mobile" if "Android" in plat else ""
        return (
            f"Mozilla/5.0 ({plat}) AppleWebKit/{saf} (KHTML, like Gecko) "
            f"Chrome/{ver}.0.{bld}.0{mobile} Safari/{saf}"
        )

    def firefox(self) -> str:
        ver = self.r.randint(60, 130)
        plat = self.pick((self.win(), self.linux(), self.mac()))
        return f"Mozilla/5.0 ({plat}; rv:{ver}.0) Gecko/20100101 Firefox/{ver}.0"

    def safari(self) -> str:
        saf = (
            f"{self.r.randint(531, 605)}.{self.r.randint(1, 50)}.{self.r.randint(1, 15)}"
        )
        ver = f"{self.r.randint(11, 18)}.{self.r.randint(0, 5)}"
        if self.r.getrandbits(1):
            return (
                f"Mozilla/5.0 ({self.mac()}) AppleWebKit/{saf} "
                f"(KHTML, like Gecko) Version/{ver} Safari/{saf}"
            )
        bld = "".join(self.r.choices(string.ascii_uppercase + string.digits, k=6))
        return (
            f"Mozilla/5.0 ({self.ios()}) AppleWebKit/{saf} "
            f"(KHTML, like Gecko) Version/{ver} Mobile/{bld} Safari/{saf}"
        )

    def opera(self) -> str:
        plat = self.pick((self.win(), self.linux()))
        locale = self.pick(_LOCALES)
        return (
            f"Opera/{self.r.randint(8, 9)}.{self.r.randint(10, 99)}."
            f"({plat}; {locale}) Presto/2.9.{self.r.randint(160, 190)} "
            f"Version/{self.r.randint(10, 12)}.00"
        )

    def ie(self) -> str:
        return (
            f"Mozilla/5.0 (compatible; MSIE {self.r.randint(7, 11)}.0; "
            f"{self.win()}; Trident/{self.r.randint(4, 7)}.{self.r.randint(0, 1)})"
        )

    def any(self) -> str:
        return self.pick((self.chrome, self.firefox, self.safari, self.opera, self.ie))()


_GENERATORS = ("chrome", "firefox", "safari", "opera", "ie")


@pytest.fixture(scope="module")
def agents() -> list[str]:
    ua = UA(seed=0)
    return [ua.any() for _ in range(2000)]


def test_generates_expected_volume(agents):
    assert len(agents) == 2000


def test_all_agents_non_empty(agents):
    assert all(a and len(a) > 20 for a in agents)


def test_no_browser_classified_as_crawler(agents):
    misclassified = [a for a in agents if is_crawler(a)]
    assert not misclassified, (
        f"{len(misclassified)} browsers flagged as crawlers, e.g. {misclassified[:3]}"
    )


@pytest.mark.parametrize("kind", _GENERATORS)
def test_each_generator_produces_browser_uas(kind):
    ua = UA(seed=1)
    samples = [getattr(ua, kind)() for _ in range(200)]
    flagged = [s for s in samples if is_crawler(s)]
    assert not flagged, f"{kind}: {len(flagged)} flagged, e.g. {flagged[:2]}"


def test_seed_determinism():
    a = [UA(seed=42).any() for _ in range(50)]
    b = [UA(seed=42).any() for _ in range(50)]
    assert a == b
