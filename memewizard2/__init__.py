from dataclasses import dataclass
from bs4 import BeautifulSoup
from typing import List
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
        "Are You",
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
    types: List[str] = None
    """What kinds of meme it is, can be 'Exploitable', an 'Image Macro', etc"""

    def complete(self):
        """Check if a meme contains all it's information"""

        return not any(x is None for x in list(self.__dict__.values()))


@dataclass
class MemeFunc:
    """Meme functions to do things like find trend history, fetch meme info, and more"""

    _name: str

    @property
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

    @property
    def url(self) -> str:
        """KnowYourMeme url for meme (can fail if meme does not exist)"""

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

    @property
    def image(self) -> str:
        """Find relevant images for a list of memes."""

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

    @property
    def info(self) -> MemeInfo:
        """KnowYourMeme data such as it's origin, the year it came out, etc."""

        r = requests.get(
            self.url,
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


class Meme:
    """Exists as a class simply to keep things sorted"""

    class YouTubeFetch:
        """Fetch memes from YouTube"""

        def __init__(self) -> None:
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

            self._meme = res
            """
            Memes collected. If you want to use these directly, the
            ``all()`` method is preferred as it comes with formatting
            """
            self.count: int = len(self._meme)
            """Number of memes collected"""

        def all(self, format: bool = True) -> list:
            """
            Returns every meme automatically created when instantiating
            YouTubeFetch. Formatting strips meme titles and removes
            any double spaces
            """

            return (
                [m.strip().replace("  ", " ") for m in self._meme]
                if format == True
                else self._meme
            )

        def query(self, sel: int):
            """Select a specific meme by its index"""

            selc = None
            resp = MemeFunc(self._meme[sel]).info.title

            try:
                selc = _Utils.subjectify(resp.split("/ ")[1]).lower()
            except IndexError:
                selc = _Utils.subjectify(resp).lower()

            return MemeFunc(selc)
