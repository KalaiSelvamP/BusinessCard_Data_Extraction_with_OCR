# BusinessCard_Data_Extraction_with_OCR

LinkedIn Profile : [Kalai Selvam](https://www.linkedin.com/in/kalai-selvam-55428126a)

## Description
The **Business Card Data Extraction** project is a Python application that utilizes **EasyOCR** and **Streamlit** to extract key information from images of business cards. The extracted data is categorized into several fields such as Name, Designation, Contact, Email, Website, Address, and Pincode. The extracted information is then stored in a SQLite database. Users can upload an image of a business card, extract its details, and save or modify the data directly through a simple and interactive web interface built with **Streamlit**.

### Key Features:
- Upload an image of a business card for text extraction.
- Use OCR (Optical Character Recognition) to extract text from the image.
- Categorize the extracted text into structured fields (e.g., Name, Contact, Email, Address).
- Display extracted information in a user-friendly interface.
- Save the extracted data to a SQLite database.
- Modify or delete saved data.
- Display saved business card images.

---

### Required Python Libraries:
The project uses the following Python libraries:
- **EasyOCR**: For Optical Character Recognition (OCR) to extract text from images.
- **Streamlit**: To create the web interface.
- **PIL (Pillow)**: To handle image processing.
- **SQLite3**: For storing extracted business card data.
- **pandas**: For data manipulation and display.
- **re (Regular Expressions)**: For pattern matching to categorize the extracted text.
- **numpy**: For array handling.
