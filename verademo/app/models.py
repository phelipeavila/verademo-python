from django.db import models

# Create your models h
class User(models.Model):
    
    class Meta:
        db_table='users'
    
    username = models.CharField(primary_key=True, max_length=100)
    password = models.CharField(max_length=100,null=True)
    password_hint = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(null=True)
    last_login = models.DateTimeField(null=True)
    real_name = models.CharField(max_length=100, null=True)
    blab_name = models.CharField(max_length=100, null=True)
    
class Blab(models.Model):
    class Meta:
        db_table='blabs'

    blabid = models.IntegerField('''max_length=11''',null=False,primary_key=True)
    blabber = models.TextField(max_length=100,null=False)
    content = models.TextField(max_length=250, null=True)
    timestamp = models.DateTimeField(null=True)
    
    def content(self):
        return self.content
    
    def postDate(self):
        return self.timestamp
    
    def getCommentCount(self):
        return self.commentCount
    
    def getAuthor(self):
        return self.blabber
     
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
        return self.real_name
    
    def getBlabName(self):
        return self.blab_name
    
    def getCreatedDate(self):
        return self.created_at
    
    def getNumListeners(self):
        return self.numberListeners
    
    def getNumListening(self):
        return self.numberListening
    
class Comment(models.Model):

    commentid = models.IntegerField(primary_key=True,null=False)
    blabid = models.IntegerField(null=False)
    blabber = models.TextField(max_length=100, null=False)
    content = models.TextField(max_length=250, null=True)
    timestamp = models.DateTimeField(null=True)

    class Meta:
        db_table = 'comments'

class Listener(models.Model):
    blabber = models.TextField(max_length=100,null=False)
    listener = models.TextField(max_length=100,null=False)
    status = models.TextField(max_length=20,null=True)

    class Meta:
        db_table = 'listeners'

class User_History(models.Model):
    class Meta:
        db_table = 'users_history'

    eventid = models.IntegerField(primary_key=True)
    blabber = models.TextField(max_length=100)
    event = models.TextField(max_length=250,null=True)
    timestamp = models.DateTimeField(null=True)

