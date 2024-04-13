import streamlit as st
import pandas as pd
from io import StringIO
from PIL import Image
import base64
from io import BytesIO

# Define necessary functions
def get_image_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue())
    return img_str.decode()


# Update the column names to be consistent with lowercase
def update_data_post_merge(data):
    # Calculate the new average RGB values
    avg_rgb_manual = data.groupby("manual_id")[["R", "G", "B"]].mean().reset_index()
    avg_rgb_manual.columns = [
        "manual_id",
        "avg_R_manual",
        "avg_G_manual",
        "avg_B_manual",
    ]
    
    # Drop the old average columns if they exist
    cols_to_drop = ["avg_R_manual", "avg_G_manual", "avg_B_manual"]
    data = data.drop(cols_to_drop, axis=1, errors='ignore')
    
    # Merge the new average values
    data = data.merge(avg_rgb_manual, on="manual_id", how="left")
    return data

# # Function to handle unselecting all clusters
# def unselect_all():
#     for key in selected_clusters:
#         selected_clusters[key] = False
#     st.experimental_rerun()

# Function to convert DataFrame to CSV for download
def convert_df_to_csv(df):
    # Create a copy of the DataFrame to avoid modifying the original data
    df_copy = df.copy()

    # Update the manual_id in the copied DataFrame based on the merged clusters
    for index, row in df_copy.iterrows():
        if row['manual_id'] in st.session_state.merged_clusters:
            df_copy.at[index, 'manual_id'] = st.session_state.merged_clusters[row['manual_id']]

    # Ensure the DataFrame is up-to-date with the latest manual IDs
    df_copy = update_data_post_merge(df_copy)

    output = StringIO()
    df_copy.to_csv(output, index=False)
    return output.getvalue()

# Initialize session state
if 'merged_clusters' not in st.session_state:
    st.session_state.merged_clusters = {}

# Load and prepare the data
data = pd.read_csv("image_data.csv", dtype={"image_id": str})
if 'manual_id' not in data.columns:
    data['manual_id'] = data['assigned_cluster_id']
data = update_data_post_merge(data)  # Calculate averages and update data

# Streamlit sidebar controls for the app
st.title("Image Cluster Viewer")

# Download functionality
if st.sidebar.button("Download Data as CSV"):
    filename = st.sidebar.text_input("Enter filename for CSV", value="cluster_data.csv")
    if filename:
        csv_data = convert_df_to_csv(data)
        st.sidebar.download_button(label="Download CSV", data=csv_data, file_name=filename, mime='text/csv')



n_images_per_row = st.sidebar.slider("Images per Row", min_value=1, max_value=15, value=7)
display_area_width = st.sidebar.slider("Display Area Width", min_value=50, max_value=100, value=80, step=5)
fixed_image_width = st.sidebar.slider("Fixed Image Width", min_value=100, max_value=300, value=140)

# Handle sorting
sort_manual_option = st.sidebar.selectbox("Sort Manual Clusters by", ["None", "Average R", "Average G", "Average B"])
if sort_manual_option != 'None':
    sort_color_manual = 'avg_' + sort_manual_option.split(' ')[1] + '_manual'
    data.sort_values(by=[sort_color_manual, 'manual_id'], ascending=[False, True], inplace=True)
else:
    data.sort_values(by='manual_id', inplace=True)

# Checkboxes for cluster selection
cluster_ids = data['manual_id'].unique()
selected_clusters = {cid: st.sidebar.checkbox(f"Cluster {cid}", value=False, key=f"cluster_checkbox_{cid}") for cid in cluster_ids}


# Merge button with confirmation
if st.sidebar.button("Merge Selected Clusters"):
    clusters_to_merge = [cid for cid, selected in selected_clusters.items() if selected]
    if clusters_to_merge:
        confirm_merge = st.sidebar.warning(f"Are you sure you want to merge clusters {clusters_to_merge}?")
        if confirm_merge:
            min_cluster_id = min(clusters_to_merge)
            data.loc[data['manual_id'].isin(clusters_to_merge), 'manual_id'] = min_cluster_id
            st.sidebar.success(f"Merged clusters {clusters_to_merge} into cluster {min_cluster_id}")

            # Store the merged clusters in the session state
            st.session_state.merged_clusters.update({cid: min_cluster_id for cid in clusters_to_merge})

            # Update the data after merging and assign the result back to data
            with st.spinner("Updating data..."):
                data = update_data_post_merge(data)
            
            # Rebuild the sidebar checkboxes after data update
            st.experimental_rerun()
    else:
        st.sidebar.error("No clusters selected for merging")


# # Unselect all clusters functionality
# if st.sidebar.button("Unselect All Clusters"):
#     for key in selected_clusters:
#         selected_clusters[key] = False
#     st.experimental_rerun()

        
# Load CSS styles
st.markdown(f'<style>{open("styles.css").read()}</style>', unsafe_allow_html=True)

# Apply the width to the main content area of Streamlit
st.markdown(f"<style>.main .block-container{{max-width: {display_area_width}%;}}</style>", unsafe_allow_html=True)

# Initialize variables
last_cluster_id = -1
image_count = 0
cluster_count = 0
cols = st.columns(n_images_per_row)

# white separator
img_path = f"img/image_white.png"
img = Image.open(img_path)
img_white = get_image_base64(img)

for index, row in data.iterrows():
    # Check if the cluster has been merged
    if row['manual_id'] in st.session_state.merged_clusters:
        # If it has, use the merged cluster ID
        manual_id = st.session_state.merged_clusters[row['manual_id']]
    else:
        # Otherwise, use the original manual ID
        manual_id = row['manual_id']

    # Update the manual_id in the DataFrame
    data.at[index, 'manual_id'] = manual_id

    # When we encounter a new cluster
    if manual_id != last_cluster_id:
        if last_cluster_id != -1:
            # Add the white separator image only if the previous cluster didn't fill the row
            if image_count % n_images_per_row != 0 and image_count != 0:
                col = cols[image_count % n_images_per_row]
                col.markdown(
                    f'<div class="cluster-bg-3" style="display: inline-flex; flex-direction: column; align-items: center; justify-content: center; width: {fixed_image_width}px; margin-right: 10px;">'
                    f'<img src="data:image/png;base64,{img_white}" style="width:{fixed_image_width}px;">'
                    f'<p style="word-wrap: break-word;"><br><br><br></p></div>',
                    unsafe_allow_html=True,
                )
                image_count += 1

        # Reset for the new cluster
        last_cluster_id = manual_id
        cluster_count += 1

    # Load and display image in the appropriate column
    col = cols[image_count % n_images_per_row]
    img_path = f"img/image_{row['image_id']}.png"
    img = Image.open(img_path)
    img_base64 = get_image_base64(img)
    # Determine the background class to use based on the cluster count
    bg_class = f"cluster-bg-{cluster_count % 2 + 1}"  # This will alternate between "cluster-bg-1" and "cluster-bg-2"
    caption = f"ID: {row['image_id']} | Real: {row['real_cluster_id']} | Assigned: {row['assigned_cluster_id']} | Manual: {manual_id}"

    # Use the slider value for the image width and ensure the div displays the background
    col.markdown(
        f'<div class="{bg_class}" style="display: inline-flex; flex-direction: column; align-items: center; justify-content: center; width: {fixed_image_width}px; margin-right: 10px;">'
        f'<img src="data:image/png;base64,{img_base64}" style="width:{fixed_image_width}px;">'
        f'<p style="word-wrap: break-word;">{caption}</p></div>',
        unsafe_allow_html=True,
    )

    image_count += 1

    # Create new columns when a row is filled
    if image_count % n_images_per_row == 0:
        cols = st.columns(n_images_per_row)

# Check if we need to add a white separator image after the last cluster
if last_cluster_id != -1 and image_count % n_images_per_row != 0:
    col = cols[image_count % n_images_per_row]
    col.markdown(
        f'<div class="cluster-bg-3" style="display: inline-flex; flex-direction: column; align-items: center; justify-content: center; width: {fixed_image_width}px; margin-right: 10px;">'
        f'<img src="data:image/png;base64,{img_white}" style="width:{fixed_image_width}px;">'
        f'<p style="word-wrap: break-word;"><br><br></p></div>',
        unsafe_allow_html=True,
    )