1. Check Copyright year in:  
   LICENSE  
   fract4dgui/application_window.py  
   manual/content/_index.md  

2. Check whether help/ needs updating. If so create a pull request using the GitHub workflow:  
   "Create a branch with updated help"  
   (Anyone installing from git or a git archive will get this copy of the manual;
    the release file will contain a regenerated copy with the release version number)

3. Confirm tests have passed. If they have not been run recently, manually trigger the GitHub workflow:  
   "Test Gnofract 4D"

4. Create a release with a new tag vX.Y[.Z] on GitHub

5. Publish the website using the GitHub workflow:  
   "Publish Gnofract 4D Website on GitHub Pages"
