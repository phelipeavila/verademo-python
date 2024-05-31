from django.db import models

# Create your models h
class User(models.Model):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    
class Blab(models.Model):

    content = models.TextField(max_length=1000)
    postDate = models.DateTimeField(auto_now_add=True)
    commentCount = models.IntegerField(default=0)
    author = models.TextField(max_length=100)
    
    def __str__(self):
        return self.id
    
    def __str2__(self):
        return self.content
    
    def __str3__(self):
        return self.postDate
    
    def __str4__(self):
        return self.commentCount
    
    def __str5__(self):
        return self.author
     
class Blabber(models.Model):
    username = models.TextField(max_length=100)
    realName = models.TextField(max_length=100)
    blabName = models.TextField(max_length=100)
    createdDate = models.DateTimeField(auto_now_add=True)
    numberListeners = models.IntegerField(default=0)
    numberListening = models.IntegerField(default=0)

    def __str__(self):
        return self.id
    
    def __str2__(self):
        return self.username
    
    def __str3__(self):
        return self.realName
    
    def __str4__(self):
        return self.blabName
    
    def __str5__(self):
        return self.createdDate
    
    def __str6__(self):
        return self.numberListeners
    
    def __str7__(self):
        return self.numberListening
    
class Comment(models.Model):
    content = models.TextField()
    timestamp = models.DateTimeField
    author = models.TextField()

    def __str__(self):
        return self.id
    
    def __str2__(self):
        return self.content
    
    def __str3__(self):
        return self.timestamp
    
    def __str4__(self):
        return self.author




