from django.db import models

# Create your models here.
class Watchlist(models.Model):
    movieID = models.CharField(primary_key=True, max_length=30)
    userID = models.CharField(max_length=20)

class Preference(models.Model):
    userID = models.CharField(primary_key=True, max_length=20)
    genre1 = models.TextField()
    genre2 = models.TextField()
    genre3 = models.TextField()

class Review(models.Model):
    reviewID = models.CharField(primary_key=True, max_length=15)
    userID = models.CharField(max_length=20)
    movieID = models.CharField(max_length=30)
    content = models.TextField()
    reviewDate = models.DateTimeField()
    
    def save(self, *args, **kwargs):
        if not self.reviewID:
            # Generate the ID if it doesn't exist
            last_id = Review.objects.order_by('-reviewID').first()
            if last_id:
                last_number = last_id.reviewID  # Extract the number from the last ID
                new_number = last_number + 1
            else:
                new_number = 1

            self.reviewID = new_number

        super().save(*args, **kwargs)
