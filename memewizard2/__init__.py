from dataclasses import dataclass
from bs4 import BeautifulSoup
import pytrends.request
import requests
import random
import json
import re


class Invalids:
    RESEARCH: "list[str]" = [
        "This submission is currently being researched and evaluated.",
        "You can help confirm this entry by contributing facts, media, and other evidence of notability and mutation.",
    ]
    NOTFOUND: str = "Page Not Found (404) - Know Your Meme"
    GALLERY: str = "Trending Videos Gallery"


class _Utils:
    stopwords = [
        "Why Is",
        "Why Does",
        "Everyone",
        "EVERYONE",
        "Why",
        "Is The",
        "How",
        "What Are",
        "What's Up",
        "With",
        "?",
        ".",
        "Are",
        "FINISHED",
    ]

    trails = ("classic", "everywhere", "what")

    def chunkify(l, n):
        for i in range(0, len(l), n):
            yield l[i : i + n]

    @classmethod
    def subjectify(self, text):
        _list = re.split(
            r"{}".format("|".join(self.trails)), "".join(text), flags=re.IGNORECASE
        )
        return "".join(_list)

    regex = re.compile("|".join(map(re.escape, stopwords)))


@dataclass
class MemeInfo:
    """A dataclass returned by functions containing information about a meme"""

    title: str
    """Meme title"""
    kym_status: str = None
    """KnowYourMeme status, not very helpful"""
    origin: str = None
    """Where the meme originated from, usually a social media"""
    year: int = None
    """Year the meme was made"""
    types: 'list[str]' = None
    """What kinds of meme it is, can be 'Exploitable', an 'Image Macro', etc"""

    def complete(self) -> bool:
        """Check if a meme contains all it's information"""

        return not any(x is None for x in list(self.__dict__.values()))


class MemeFunc:
    """
    Meme functions to do things like find trend history, fetch meme info, and more
    If the meme does not exist in KnowYourMeme, fetching meme info will not work.
    """

    def __init__(self, name) -> None:
        self._name = name
    
    def __repr__(self) -> str:
        return self._name

    def history(self) -> list:
        """Google Search trends"""

        trend = pytrends.request.TrendReq()
        trend.build_payload(
            [_Utils.subjectify(self._name).lower()],
            timeframe="today 1-m",
            cat="0",
            geo="US",
        )

        search = trend.interest_over_time()
        return [e[0] for e in search.values.tolist()]

    def url(self) -> str:
        """KnowYourMeme url for meme"""

        doc = requests.get(
            "https://www.google.com/search?q={}&surl=1&safe=active&ssui=on".format(
                f"{self._name} know your meme"
            ).replace(" ", "+")
        )
        return (
            [
                link["href"]
                for link in BeautifulSoup(doc.text, "html.parser").find_all(
                    "a", href=True
                )
                if "knowyourmeme.com" in link["href"]
                and link["href"].find("cultures") == -1
            ][0]
            .split("?q=")[1]
            .split("&sa")[0]
        )

    def image(self) -> str:
        """Relevant image for meme"""

        r = requests.get(
            "https://www.google.com/search?q={}&rlz=1CAOUAQ_enUS980&source=lnms&tbm=isch&biw=1517&bih=750&dpr=0.9&surl=1&safe=active&ssui=on#imgrc=1QhXmjkgq_MRQM".format(
                self._name
            )
        ).text
        soup = BeautifulSoup(r, "html.parser")
        images = soup.find_all("img")

        return "https://" + re.split(
            r"https://|http://", images[random.randrange(1, len(images))]["src"]
        )[-1].replace("&s", "")

    def info(self) -> MemeInfo:
        """KnowYourMeme data such as it's origin, the year it came out, etc."""

        r = requests.get(
            self.url(),
            headers={
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"
            },
        )
        s = BeautifulSoup(r.text, "html.parser")
        title = s.find("title").text.split(" |")[0]

        try:
            st = s.find("div", {"class": ["details"]}).text.split("\n\n")
        except AttributeError:
            st = [""]
        while "" in st:
            st.remove("")

        st = [_st.replace(":", "").replace("\n", "") for _st in st]
        st = list(_Utils.chunkify(st, 2))
        st.insert(0, ["Name", title])

        if Invalids.RESEARCH in st:
            st.remove(Invalids.RESEARCH)

        json = {
            item[0]: item[1].split(",") if item[0] == "Type" else item[1] for item in st
        }
        return MemeInfo(*list(json.values()))

def fetch_memes() -> 'list[MemeFunc]':
    '''Fetch memes from YouTube'''

    r = requests.get("https://www.youtube.com/c/LessonsinMemeCulture/videos")
    big_response = json.loads(
        r.text.split("var ytInitialData =")[1].split(";</script>")[0]
    )
    filtere = big_response["contents"]["twoColumnBrowseResultsRenderer"][
        "tabs"
    ][1]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0][
        "itemSectionRenderer"
    ][
        "contents"
    ][
        0
    ][
        "gridRenderer"
    ][
        "items"
    ]
    res = []
    for i in range(len(filtere)):
        try:
            string = (
                filtere[i]["gridVideoRenderer"]["title"]["runs"][0]["text"]
                .replace("“", '"')
                .replace("”", '"')
            )
            token = _Utils.regex.sub("", string)
            words = re.findall('"([^"]*)"', string)
            if len(words) > 0:
                meme = "".join([s.split("_")[0] for s in words[0]])
                res.append(meme)
            else:
                res.append(_Utils.subjectify(token))
        except KeyError:
            break

    return [MemeFunc(m.strip().replace("  ", " ").split("/ ")[1] if "/" in m else m.strip().replace("  ", " ")) for m in res]
