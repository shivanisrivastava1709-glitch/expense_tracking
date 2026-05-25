# Command to run on windows machine
## 1. first reach out to the folder location and then go inside the project folder then open the folder in visual studio code and then open a terminal and type `claude` on terminal
## 2. login into claude


### run in one single command in terminal of vscode on windows machine
### `!source venv/Scripts/activate && which python && python -m pip -V && pip install -r requirements.txt`

### in th elogs you should see that the python installed within your current project's venv directoryt is being picked up and also the packages are installed locally within venv/lib directory 

### if venv is not getting picked up automatically then execute this command once and then it will activate on that session

### (Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& c:\Users\shiva\OneDrive\Documents\Claude\expense-tracker\expense-tracker\venv\Scripts\Activate.ps1)




### after this close the current terminal and open a new one .. and this time you should see a (venv) symbol before the terminal that means your virtual env has been loaded and ready to work with 

### type `claude` in new terminal to get the claude terminal prompt and then use `!which python` command to find out which python path is shown --> it should be from your project path


### 


