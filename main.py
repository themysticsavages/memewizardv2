import memewizard2
import colorama

memes = memewizard2.Meme.YouTubeFetch()
for i in range(memes.count):
    print(memes.query(i).history)
