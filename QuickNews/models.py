from django.db import models
from django.utils import timezone

class ArticleSummary(models.Model):
    title = models.CharField(max_length=500)
    short_title = models.CharField(max_length=50, blank=True)  # For history display
    authors = models.CharField(max_length=200, blank=True)
    publish_date = models.CharField(max_length=50, blank=True)
    summary = models.TextField()
    top_image = models.URLField(blank=True, null=True)
    sentiment = models.CharField(max_length=20)
    url = models.URLField(unique=True) # It's good practice to make the URL unique
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        
    def save(self, *args, **kwargs):
        # Generate short title for history display (max 4 words)
        if self.title and not self.short_title:
            words = self.title.split()
            if len(words) > 4:
                self.short_title = ' '.join(words[:4]) + '...'
            else:
                self.short_title = self.title
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title