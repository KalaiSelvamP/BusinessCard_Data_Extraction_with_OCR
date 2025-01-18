import easyocr
from PIL import Image
import re
import io
import pandas as pd
import streamlit as st
import numpy as np
import sqlite3
from streamlit_option_menu import option_menu


# Function to extract text and image data from the uploaded image
def extract_text_and_image(image_input):
    # Open the image from the file input
    extracted_image = Image.open(image_input)

    #Convert image into bytes
    byte_stream = io.BytesIO()
    extracted_image.save(byte_stream, format="PNG")

    # Get the binary data from the byte stream
    image_bi_value = byte_stream.getvalue()
    ex_img_arr = np.array(extracted_image) # Convert image into numpy array for OCR processing

    # Initialize EasyOCR reader and extract text from the image
    reader = easyocr.Reader(['en']) # Using English language model
    results = reader.readtext(ex_img_arr) # Extract the text from the image

    # Extract the text from the results
    extracted_text = [result[1] for result in results]

    return extracted_text,image_bi_value # Return extracted text and image binary data


# Function to categorize the extracted text into specific fields
def categorize_extracted_text(extracted_text):

    # Initialize dictionary to store categorized text data
    extracted_text_dict={"NAME":[] ,"DESIGNATION":[],"COMPANY_NAME":[],"CONTACT":[],
                         "EMAIL":[],"WEBSITE":[],"ADDRESS":[],"PINCODE":[]}


    # Assuming first two entries are name and designation
    extracted_text_dict['NAME'].append(extracted_text[0])
    extracted_text_dict['DESIGNATION'].append(extracted_text[1])

    # Regular expressions to identify specific patterns like email, phone, pincode, etc.
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    pincode_pattern = r'\b\d{6,}\b'
    address_pattern = re.compile(r'\d+\s[A-Za-z]+\s[A-Za-z\s,]+')

    # Iterate over the extracted text and categorize it
    for i in range(2,len(extracted_text)): # Start from index 2 (skipping name and designation)
        
        if re.match(email_pattern, extracted_text[i]):
            extracted_text_dict["EMAIL"].append(extracted_text[i])

        elif extracted_text[i].startswith("+") or (extracted_text[i].replace("-",'').isdigit()):
            extracted_text_dict["CONTACT"].append(extracted_text[i])

        elif 'WWW' in extracted_text[i] or "www" in extracted_text[i] or "wWw" in extracted_text[i] or "Www" in extracted_text[i] or "wwW" in extracted_text[i]:
            lower_txt=extracted_text[i].lower()
            extracted_text_dict["WEBSITE"].append(lower_txt)

        elif re.match(address_pattern, extracted_text[i]):
            remove_punct = re.sub(r'[,;]','',extracted_text[i])
            extracted_text_dict["ADDRESS"].append(remove_punct)

        elif re.findall(pincode_pattern, extracted_text[i]):
            address_parts = extracted_text[i].split()

            # Check if the last part is the pincode
            if address_parts[-1].isdigit():
                if len(address_parts) > 1:
                    # If yes, assign the rest to ADDRESS and the pincode to PINCODE
                    extracted_text_dict["ADDRESS"].append(' '.join(address_parts[:-1]))
                extracted_text_dict["PINCODE"].append(address_parts[-1])
            else:
                # If no pincode found, considering the whole string as PINCODE
                extracted_text_dict["PINCODE"].append(address_parts[0])

        else:
            extracted_text_dict["COMPANY_NAME"].append(extracted_text[i])


    # Function to format multiple contacts into a single string
    def format_contact(contact_list):
        if isinstance(contact_list, list):
            formatted_contacts = ', '.join(contact_list) # Join multiple contacts with commas
            # Return the formatted string inside a list
            return [formatted_contacts]
    
    extracted_text_dict["CONTACT"] = format_contact(extracted_text_dict["CONTACT"])
    
    # Concatenate values for keys with multiple string values (i.e Concatenate texts for categories that have multiple entries )
    
    for key, values in extracted_text_dict.items():
        if key =="CONTACT":
            pass
        elif len(values) > 0:
            join_text=" ".join(values)
            extracted_text_dict[key] =[join_text]
        else:
            values="NA"
            extracted_text_dict[key] = [values] # Assign "NA" if no value found for the field

    return extracted_text_dict # Return the categorized text data



# Main function to run the Streamlit app
def main():

    # Set page configuration for Streamlit app layout
    st.set_page_config(layout="wide")

    # Add custom CSS for title styling
    st.markdown("""
        <style>
        .main-title {
            font-size: 3em;
            color: #db144c; /* Change this to your preferred color */
            text-align: center;
            font-weight: bold;
            margin-bottom: 0.5em;
        }
        </style>
        <h1 class="main-title">Business Card Data Extraction</h1>
        """, unsafe_allow_html=True)
    
    
    # Sidebar menu options using streamlit_option_menu
    with st.sidebar:
        page = option_menu(
            "Menu",
            ["Upload and Modify", "Saved Data", "Delete Data"],
            icons=["cloud-upload", "database", "trash"],  # Icons for the options
            menu_icon="cast",  # Menu icon
            default_index=0,  # Default selected option
        )

    # Page for uploading and modifying business card data
    if page=="Upload and Modify":

        # Connect to SQLite database
        conn = sqlite3.connect("businesscard_DB.db")
        cursor = conn.cursor()
        
        # Create a table if it doesn't exist for storing business card details
        create_query = '''CREATE TABLE IF NOT EXISTS buisnesscard_details(name varchar(225),
                                                                                designation varchar(225),
                                                                                company_name varchar(225),
                                                                                contact varchar(225),
                                                                                email varchar(225),
                                                                                website text,
                                                                                address text,
                                                                                pincode varchar(225),
                                                                                image text,
                                                                                CONSTRAINT unique_name_company UNIQUE (name, company_name))'''        
        cursor.execute(create_query)
        conn.commit()

        # Function to delete a record from the database
        def delete_row(name, company_name):
            cursor.execute("DELETE FROM buisnesscard_details WHERE name = ? AND company_name = ?", (name, company_name))
            conn.commit()


        # Upload an image file through Streamlit's file uploader
        uploaded_file = st.file_uploader("Choose an image...",type=['png','jpg','jpeg'])
        
        if uploaded_file is not None:
            # Display the uploaded image
            st.image(uploaded_file,caption='Uploaded Image',width=400)
            st.write("")

            # Extract text and image data
            extract_text,extract_img= extract_text_and_image(uploaded_file)

            # Categorize the extracted text into structured fields
            categorized_text=categorize_extracted_text(extract_text)

            if categorized_text:
                st.success('Extraction Success')
            

            # Display the extracted and categorized text data in a dataframe
            st.write("Extracted Text:")
            df1=pd.DataFrame(categorized_text)
            img_bi_dict={'IMAGE':[extract_img]}
            df2=pd.DataFrame(img_bi_dict)
            df3 = pd.concat([df1, df2], axis=1)
            st.dataframe(df3)

            # Function to save the extracted data into the database
            def save_data(df):
                try:
                    insert_query = '''INSERT INTO buisnesscard_details(name, designation,
                                                                    company_name,contact,
                                                                    email, website, address,
                                                                    pincode, image)
                                                                    values(?,?,?,?,?,?,?,?,?)'''

                    df_data = df.values.tolist()[0] # Convert dataframe row to list
                    cursor.execute(insert_query,df_data) # Insert data into database
                    conn.commit()
                    return "Saved Successfully"                
                except sqlite3.IntegrityError as e: # Handling integrity error (i.e duplicate entry)
                    return "Duplicate entry detected"



            # Button to save the extracted data to the database      
            if st.button("Save data"):
                result = save_data(df3)
                if result == "Saved Successfully":
                    st.success("Data saved successfully!")
                else:
                    st.error("Duplicate entry detected")

            # Initialize session state for modified data
            st.session_state.df3 = df3
            
            # Form for modifying the extracted data
            with st.form(key='modify_form'):
                st.write("Modify the data below:")
                edited_df = st.data_editor(st.session_state.df3)

                # Update session state with edited data
                st.session_state.df3 = edited_df

                # Submit button for the edited data form
                submit_button = st.form_submit_button(label='Save modified data')
                if submit_button:
                    # Delete old data and insert modified data into the database
                    name=df3['NAME'].iloc[0]
                    company_name=df3['COMPANY_NAME'].iloc[0]
                    delete_query = '''DELETE FROM buisnesscard_details WHERE name = ? AND company_name = ?'''

                    try:
                        # Execute the DELETE query with the parameters
                        cursor.execute(delete_query, (name, company_name))
                        conn.commit()
                        # Insert modified data
                        insert_query = '''INSERT INTO buisnesscard_details(name, designation,
                                                                        company_name,contact,
                                                                        email, website, address,
                                                                        pincode, image)
                                                                        values(?,?,?,?,?,?,?,?,?)'''

                        df_data = st.session_state.df3.values.tolist()[0]
                        cursor.execute(insert_query,df_data)
                        conn.commit()
                        st.success("Modified Data saved successfully!")
                        conn.close()
                        
                    except sqlite3.Error as e:
                        st.error("Not able to update Modified data")
                        #return "No duplicate data"
                    
                    

    # Page to view saved data
    elif page=="Saved Data":

        # Making connection to SQL Lite
        conn = sqlite3.connect("businesscard_DB.db")
        cursor = conn.cursor()

        # Query to load data from the database
        query = "SELECT * FROM buisnesscard_details"
        saved_data = pd.read_sql(query, conn)
        st.dataframe(saved_data)

        # Select box to choose a name and company to view its image
        st.write("Choose Name and Company")
        row1_col1, row1_col2 = st.columns(2)

        with row1_col1:
            selected_name = st.selectbox("Select Name", saved_data['name'].unique())

        with row1_col2:
            selected_company_name = st.selectbox("Select Company Name", saved_data[saved_data['name'] == selected_name]['company_name'].unique())


        image_button = st.button("Show Image")
        
        # Initialize session state flag for showing the form
        if 'show_form' not in st.session_state:
            st.session_state.show_form = False

        # Modify button to show the form
        if st.button("Modify"):
            st.session_state.show_form = True
        
        if st.session_state.show_form and selected_name != 'None' and selected_company_name != 'None':
            df4 = saved_data[(saved_data['name'] == selected_name) & (saved_data['company_name'] == selected_company_name)]
            st.session_state.df4 = df4
            with st.form(key='modify_saved_form'):
                st.write("Modify the data below:")
                edited_df1 = st.data_editor(st.session_state.df4)
                st.session_state.df4 = edited_df1
                submit_button = st.form_submit_button(label='Save modified data')
                if submit_button:
                    # Execute the DELETE query with the parameters
                    name=df4['name'].iloc[0]
                    company_name=df4['company_name'].iloc[0]
                    delete_query = '''DELETE FROM buisnesscard_details WHERE name = ? AND company_name = ?'''
                    cursor.execute(delete_query, (name,company_name))
                    conn.commit()

                    # Insert or update the modified data in the SQLite database
                    insert_query = '''INSERT INTO buisnesscard_details(name, designation,
                                                                    company_name,contact,
                                                                    email, website, address,
                                                                    pincode, image)
                                                                    values(?,?,?,?,?,?,?,?,?)'''

                    df_data = st.session_state.df4.values.tolist()[0]
                    cursor.execute(insert_query,df_data)
                    conn.commit()
                    st.session_state.show_form = False
                    st.success('Modified data saved')

        else:
            pass     
        
        if image_button:
            image_data = None
            # Function to display image from binary data
            def display_image_from_binary(image_data):
                image = Image.open(io.BytesIO(image_data))
                col1, col2, col3 = st.columns([1, 2, 1])  # Adjust column ratios as needed
                with col2:
                    st.image(image, caption='Uploaded Image', width=400)


            # Retrieve and display image based on selected name and company
            cursor.execute("SELECT image FROM buisnesscard_details WHERE name = ? AND company_name = ?", (selected_name, selected_company_name))
            result = cursor.fetchone()
            if result is not None:
                image_data = result[0]
                # Display the image
                display_image_from_binary(image_data)
            else:
                st.info("No image found for the selected name and company name")

        conn.close()

        
    # Page for deleting saved data
    elif page=="Delete Data":
        
        # Making connection to SQL Lite
        conn = sqlite3.connect("businesscard_DB.db")
        cursor = conn.cursor()
        
        # Function to delete rows from SQLite based on name and designation
        def delete_row(name, company_name):
            cursor.execute("DELETE FROM buisnesscard_details WHERE name = ? AND company_name = ?", (name, company_name))
            conn.commit()


        # Query to load data from the database
        query = "SELECT * FROM buisnesscard_details"
        saved_data = pd.read_sql(query, conn)
        st.write("All Data:")
        st.write(saved_data)

        # Select box to choose name and company to delete
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            selected_name = st.selectbox("Select Name", saved_data['name'].unique())

        with row1_col2:
            selected_company_name = st.selectbox("Select Company Name", saved_data[saved_data['name'] == selected_name]['company_name'].unique())

        # Delete button to delete selected record
        if st.button("Delete"):
            # Call delete_row function
            delete_row(selected_name, selected_company_name)
            st.success("Data deleted successfully!")

        conn.close() # Close the database connection

# Run the main function when the script is executed
if __name__ == "__main__":
    main()