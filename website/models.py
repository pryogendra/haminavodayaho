from django.db import models

class Feature(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    
    def __str__(self):
        return self.title


class Screenshot(models.Model):
    image = models.ImageField(upload_to='screenshots/')
    alt_text = models.CharField(max_length=255, default='Screenshot')

    def __str__(self):
        return self.alt_text


class ContactMessage(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.email}"


class AboutSection(models.Model):
    heading = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='about/', null=True, blank=True)
    image2 = models.ImageField(upload_to='about/', null=True, blank=True)

    def __str__(self):
        return self.heading


class HeroSection(models.Model):
    headline = models.CharField(max_length=255)
    subtext = models.TextField()

    def __str__(self):
        return self.headline
    
    
class myApkFile(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='apk/')

    def __str__(self):
        return self.title

