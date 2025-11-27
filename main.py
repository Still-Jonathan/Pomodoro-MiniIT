import tkinter
from tkinter import ttk
from tkinter import messagebox

def enterData():
    accepted = acceptVar.get()
    
    if accepted == "Accepted":
        firstName = firstNameEntry.get()
        lastName = lastNameEntry.get()
        
        if firstName and lastName:
            title = titleCombobox.get()
            age = ageSpinbox.get()
            nationality = nationalityCombobox.get()
            
            registrationStatus = regStatusVar.get()
            numCourses = numCoursesSpinbox.get()
            numSemesters = numSemestersSpinbox.get()
            
            print("First name: ", firstName, "Last name: ", lastName)
            print("Title: ", title, "Age: ", age, "Nationality: ", nationality)
            print("# Courses: ", numCourses, "# Semesters: ", numSemesters)
            print("Registration status", registrationStatus)
            print("------------------------------------------")
        else:
            tkinter.messagebox.showwarning(title="Error", message="First name and last name are required.")
    else:
        tkinter.messagebox.showwarning(title="Error", message="You have not accepted the terms")

window = tkinter.Tk()
window.title("Data Entry Form")

frame = tkinter.Frame(window)
frame.pack()

userInfoFrame = tkinter.LabelFrame(frame, text="User Information")
userInfoFrame.grid(row=0, column=0, padx=20, pady=10)

firstNameLabel = tkinter.Label(userInfoFrame, text="First Name")
firstNameLabel.grid(row=0, column=0)
lastNameLabel = tkinter.Label(userInfoFrame, text="Last Name")
lastNameLabel.grid(row=0, column=1)

firstNameEntry = tkinter.Entry(userInfoFrame)
lastNameEntry = tkinter.Entry(userInfoFrame)
firstNameEntry.grid(row=1, column=0)
lastNameEntry.grid(row=1, column=1)

titleLabel = tkinter.Label(userInfoFrame, text="Title")
titleCombobox = ttk.Combobox(userInfoFrame, values=["", "Mr.", "Ms.", "Dr."])
titleLabel.grid(row=0, column=2)
titleCombobox.grid(row=1, column=2)

ageLabel = tkinter.Label(userInfoFrame, text="Age")
ageSpinbox = tkinter.Spinbox(userInfoFrame, from_=18, to=110)
ageLabel.grid(row=2, column=0)
ageSpinbox.grid(row=3, column=0)

nationalityLabel = tkinter.Label(userInfoFrame, text="Nationality")
nationalityCombobox = ttk.Combobox(userInfoFrame, values=["Africa", "Antarctica", "Asia", "Europe", "North America", "Oceania", "South America"])
nationalityLabel.grid(row=2, column=1)
nationalityCombobox.grid(row=3, column=1)

for widget in userInfoFrame.winfo_children():
    widget.grid_configure(padx=10, pady=5)

coursesFrame = tkinter.LabelFrame(frame)
coursesFrame.grid(row=1, column=0, sticky="news", padx=20, pady=10)

registeredLabel = tkinter.Label(coursesFrame, text="Registration Status")

regStatusVar = tkinter.StringVar(value="Not Registered")
registeredCheck = tkinter.Checkbutton(coursesFrame, text="Currently Registered",
                                      variable=regStatusVar, onvalue="Registered", offvalue="Not registered")

registeredLabel.grid(row=0, column=0)
registeredCheck.grid(row=1, column=0)

numCoursesLabel = tkinter.Label(coursesFrame, text="# Completed Courses")
numCoursesSpinbox = tkinter.Spinbox(coursesFrame, from_=0, to='infinity')
numCoursesLabel.grid(row=0, column=1)
numCoursesSpinbox.grid(row=1, column=1)

numSemestersLabel = tkinter.Label(coursesFrame, text="# Semesters")
numSemestersSpinbox = tkinter.Spinbox(coursesFrame, from_=0, to="infinity")
numSemestersLabel.grid(row=0, column=2)
numSemestersSpinbox.grid(row=1, column=2)

for widget in coursesFrame.winfo_children():
    widget.grid_configure(padx=10, pady=5)

termsFrame = tkinter.LabelFrame(frame, text="Terms & Conditions")
termsFrame.grid(row=2, column=0, sticky="news", padx=20, pady=10)

acceptVar = tkinter.StringVar(value="Not Accepted")
termsCheck = tkinter.Checkbutton(termsFrame, text="I accept the terms and conditions.",
                                 variable=acceptVar, onvalue="Accepted", offvalue="Not Accepted")
termsCheck.grid(row=0, column=0)

button = tkinter.Button(frame, text="Enter data", command=enterData)
button.grid(row=3, column=0, sticky="news", padx=20, pady=10)
 
window.mainloop()