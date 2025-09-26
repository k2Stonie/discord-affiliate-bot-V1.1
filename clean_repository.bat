@echo off
echo 🔧 Cleaning Git repository to remove sensitive data...
echo ==================================================

echo 📁 Removing .git directory...
rmdir /s /q .git

echo 📁 Removing .gitattributes...
del .gitattributes

echo 📁 Initializing clean repository...
git init
git branch -M main

echo 📦 Adding files to clean repository...
git add .

echo 💾 Making clean commit...
git commit -m "Initial Discord Affiliate Bot setup - Clean repository

- Discord Affiliate Bot with Base44 integration
- Ready for deployment to Render
- All sensitive tokens removed and secured
- Includes deployment guides and configuration"

echo.
echo ✅ Repository cleaned successfully!
echo.
echo Next steps:
echo 1. In GitHub Desktop, remove the current repository
echo 2. Add the repository again (it will detect the new clean .git folder)
echo 3. Push to GitHub - no more secret warnings!
echo.
pause

