from django.db import models

# Create your models h
class User(models.Model):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    hint = models.CharField(max_length=100, null=True)
    dateCreated = models.DateField(null=True)
    lastLogin = models.DateField(null=True)
    blabName=models.CharField(max_length=100, null=True)
    realName=models.CharField(max_length=100, null=True)
    
class Blab(models.Model):
    content = models.TextField(max_length=1000)
    postDate = models.DateTimeField(auto_now_add=True)
    commentCount = models.IntegerField(default=0)
    author = models.TextField(max_length=100)
    
    def getID(self):
        return self.id
    
    def content(self):
        return self.content
    
    def postDate(self):
        return self.postDate
    
    def getCommentCount(self):
        return self.commentCount
    
    def getAuthor(self):
        return self.author
     
class Blabber(models.Model):
    username = models.TextField(max_length=100)
    realName = models.TextField(max_length=100)
    blabName = models.TextField(max_length=100)
    createdDate = models.DateTimeField(auto_now_add=True)
    numberListeners = models.IntegerField(default=0)
    numberListening = models.IntegerField(default=0)
    
    def user(self):
        return self.username
    
    def getRealName(self):
        return self.realName
    
    def getBlabName(self):
        return self.blabName
    
    def getCreatedDate(self):
        return self.createdDate
    
    def getNumListeners(self):
        return self.numberListeners
    
    def getNumListening(self):
        return self.numberListening
    
class Comment(models.Model):
    username = models.TextField(max_length=100)
    content = models.TextField()
    timestamp = models.DateTimeField
    author = models.TextField()

    def commentUser(self):
        return self.username
    
    def getCommentContent(self):
        return self.content
    
    def postedTime(self):
        return self.timestamp
    
    def getCommentAuthor(self):
        return self.author




