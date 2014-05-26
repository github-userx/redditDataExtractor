from image import Image
import requests


class ImgurLinkTypeEnum():
    DIRECT = 1
    SINGLE_PAGE = 2
    ALBUM = 3


class ImgurImageFinder():
    __slots__ = ('URL', 'CLIENT_ID', 'imgurLinkType')

    def __init__(self, URL):

        self.URL = URL
        self.CLIENT_ID = 'e0ea61b57d4c3c9'  # imgur client ID for API access
        self.imgurLinkType = self.getImgurLinkType()

    def validURLImage(self, url):
        #Determine if the file is good to download.
        #Status Code must be 200 (valid page)
        #Must have valid data response
        headers = {'Authorization': 'Client-ID ' + self.CLIENT_ID}
        apiURL = 'https://api.imgur.com/3/'
        if self.imgurLinkType == ImgurLinkTypeEnum.DIRECT:
            imgurHashID = url[url.rfind('/') + 1:url.rfind('.')]
            apiURL += 'image/' + imgurHashID + '.json'
        elif self.imgurLinkType == ImgurLinkTypeEnum.SINGLE_PAGE:
            imgurHashID = url[url.rfind('/') + 1:]
            apiURL += 'image/' + imgurHashID + '.json'
        else:
            imgurHashID = url[url.rfind('/') + 1:]
            apiURL += 'album/' + imgurHashID + '.json'
        response = requests.get(apiURL, headers=headers, stream=True)
        json = response.json()
        status = json.get('status')
        success = json.get('success')
        if (status is None and json.get('error') is not None) or (not success):
            return False, None
        elif (status is not None and status == 200) and (
                json.get('image') is not None or json.get('data') is not None) and success:
            return True, response
        else:
            return False, None

    def getImageURLs(self, url):
        valid, response = self.validURLImage(url)
        imageURLs = []
        if valid:
            if self.imgurLinkType == ImgurLinkTypeEnum.DIRECT:
                data = response.json().get('data')
                if data is not None:
                    link = data.get('link')
                    if link is not None:
                        imageURLs.append(link)
            elif self.imgurLinkType == ImgurLinkTypeEnum.SINGLE_PAGE:
                image = response.json().get('image')
                if image is not None:
                    links = image.get('links')
                    if links is not None:
                        original = links.get('original')
                        imageURLs.append(original)
            else:
                data = response.json().get('data')
                if data is not None:
                    images = data.get('images')
                    if images is not None:
                        for image in images:
                            link = image.get('link')
                            if link is not None:
                                imageURLs.append(link)
        return imageURLs

    def getImgurLinkType(self):
        if "i.imgur.com" in self.URL:
            return ImgurLinkTypeEnum.DIRECT
        elif "imgur.com/a/" in self.URL:
            return ImgurLinkTypeEnum.ALBUM
        else:
            return ImgurLinkTypeEnum.SINGLE_PAGE

    @staticmethod
    def getFileType(URL):
        fileType = URL[URL.rfind("."):]
        return fileType

    def makeImage(self, user, postID, URL, redditPostURL, defaultPath, count):
        response = requests.get(URL, stream=True)
        fileType = self.getFileType(URL)
        if response.status_code == 200:
            return Image(user, postID, fileType, defaultPath, URL, redditPostURL, response.iter_content(4096),
                         str(count))
        else:
            return None

    def getImages(self, post, defaultPath):
        images = []
        imageURLs = self.getImageURLs(post.url)
        count = 1
        for imageURL in imageURLs:
            params = (post.author.name, post.id, imageURL, post.permalink, defaultPath, count)
            image = self.makeImage(*params)
            if image is not None:
                images.append(image)
                count += 1
        return images