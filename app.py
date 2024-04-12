import streamlit as st
import pandas as pd
from PIL import Image
import base64
from io import BytesIO


def get_image_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue())
    return img_str.decode()


# Load image data and convert 'image_id' to string
data = pd.read_csv("image_data.csv", dtype={"image_id": str})
data.sort_values(by="assigned_cluster_id", inplace=True)

# Calculate the average RGB values for each assigned cluster
avg_rgb = data.groupby("assigned_cluster_id")[["R", "G", "B"]].mean().reset_index()
avg_rgb.columns = ["assigned_cluster_id", "avg_R", "avg_G", "avg_B"]
data = data.merge(avg_rgb, on="assigned_cluster_id")

# Streamlit page configuration
st.title("Image Cluster Viewer")
# Sidebar controls
n_images_per_row = st.sidebar.slider("Images per Row", min_value=1, max_value=15, value=7)
display_area_width = st.sidebar.slider("Display Area Width", min_value=50, max_value=100, value=80, step=5)

# Apply the width to the main content area of Streamlit
st.markdown(f"<style>.main .block-container{{max-width: {display_area_width}%;}}</style>", unsafe_allow_html=True)

fixed_image_width = st.sidebar.slider(
    "Fixed Image Width", min_value=100, max_value=300, value=140
)

# Sort clusters by average RGB values
sort_option = st.sidebar.selectbox(
    "Sort Clusters by", ["None", "Average R", "Average G", "Average B"]
)
if sort_option != "None":
    sort_color = (
        "avg_" + sort_option.split(" ")[1]
    )  # Extracts 'R', 'G', or 'B' from the option
    data.sort_values(by=sort_color, ascending=False, inplace=True)

cluster_filter = st.sidebar.selectbox(
    "Filter by Assigned Cluster ID",
    ["All"] + sorted(data["assigned_cluster_id"].unique()),
)

# Define CSS
css = """
<style>
.cluster-bg-1 {
    background-color: #faf3e0;
    padding: 5px;
    border-radius: 5px;
    text-align: center;
    margin-bottom: 5px;
}
.cluster-bg-2 {
    background-color: #d9e2ec;
    padding: 5px;
    border-radius: 5px;
    text-align: center;
    margin-bottom: 5px;
}
.cluster-bg-3 {
    background-color: #FFFFFF;
    padding: 5px;
    border-radius: 5px;
    text-align: center;
    margin-bottom: 5px;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)


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
    if cluster_filter != "All" and row["assigned_cluster_id"] != cluster_filter:
        continue

    # When we encounter a new cluster
    if row["assigned_cluster_id"] != last_cluster_id:
        if last_cluster_id != -1:
            # Add the white separator image only if the previous cluster didn't fill the row
            if image_count % n_images_per_row != 0 and image_count != 0:
                col = cols[image_count % n_images_per_row]
                # col.image("img/image_white.png", width=fixed_image_width, caption="")
                col.markdown(
                f'<div class="cluster-bg-3" style="display: inline-flex; flex-direction: column; align-items: center; justify-content: center; width: {fixed_image_width}px; margin-right: 10px;">'
                f'<img src="data:image/png;base64,{img_white}" style="width:{fixed_image_width}px;">'
                f'<p style="word-wrap: break-word;"><br><br></p></div>',
                unsafe_allow_html=True,
            )
                image_count += 1

        # Reset for the new cluster
        last_cluster_id = row["assigned_cluster_id"]
        cluster_count += 1


    # Load and display image in the appropriate column
    col = cols[image_count % n_images_per_row]
    img_path = f"img/image_{row['image_id']}.png"
    img = Image.open(img_path)
    img_base64 = get_image_base64(img)
    # Determine the background class to use based on the cluster count
    bg_class = f"cluster-bg-{cluster_count % 2 + 1}"  # This will alternate between "cluster-bg-1" and "cluster-bg-2"
    caption = f"ID: {row['image_id']} | Real: {row['real_cluster_id']} | Assigned: {row['assigned_cluster_id']}"

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
    col.image("img/image_white.png", width=100, caption="")
