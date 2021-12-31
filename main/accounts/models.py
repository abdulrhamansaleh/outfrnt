from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self,email,username,password=None):
        if not email:
            raise ValueError("Email Required")
        if not username:
            raise ValueError("User Name required")

        user = self.model(
            email=self.normalize_email(email),
            username=username, 
            )
        user.is_coach = False
        user.is_client = False
        user.is_newClient = False 

        user.set_password(password)
        user.save(using=self._db)
        return user

    # creating a super user (admin)
    def create_superuser(self,email,username,password):
        user = self.create_user(
            email = self.normalize_email(email),
            password = password,
            username = username,
            )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    # email for clients of coaches 
    email = models.EmailField(verbose_name =('email'),max_length=60,unique=True)
    # user name used for clients company name 
    username = models.CharField(max_length=30,unique=True)
    # referencing login and join information 
    date_joined = models.DateTimeField(verbose_name ='date joined',auto_now_add=True)
    last_login = models.DateTimeField(verbose_name = 'last login',auto_now=True)
     # making sure user is accessible
    is_active = models.BooleanField(default=True)
    # ensuring the permissions of all users are restricited 
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # setting a coach permission for view controls 
    is_coach = models.BooleanField(default=False)

    # existing clients that have already completed questionaire 
    is_client = models.BooleanField(default=False)

    # new clients have been approved to complete a questionnaire 
    is_newClient = models.BooleanField(default=False) 

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    # display user information 
    def __str__(self):
        return "Username:" + self.username 

    def has_perm(self,perm,obj = None):
        return self.is_admin
    
    def has_module_perms(self,app_label):
        return True
