"""Streamlit frontend for Video Extractor application."""

import os
import streamlit as st
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Video Extractor",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration - for demo purposes, we'll simulate the API
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEMO_MODE = True  # Enable demo mode for Streamlit Cloud deployment

def check_api_health() -> bool:
    """Check if the FastAPI backend is running."""
    if DEMO_MODE:
        return False  # API not available in demo mode
    try:
        response = requests.get(f"{API_BASE_URL}/healthz", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def simulate_video_processing(video_file) -> Dict[str, Any]:
    """Simulate video processing for demo mode."""
    import time
    
    # Simulate processing time
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(100):
        progress_bar.progress(i + 1)
        if i < 30:
            status_text.text("🎵 Extracting audio...")
        elif i < 70:
            status_text.text("🗣️ Transcribing speech...")
        else:
            status_text.text("🤖 Generating summary...")
        time.sleep(0.05)
    
    # Return simulated results
    sample_transcript = """Welcome to our video presentation. Today we'll be discussing the importance of artificial intelligence in modern business applications. 

AI has revolutionized how we process data, make decisions, and interact with customers. Machine learning algorithms can analyze vast amounts of information in seconds, providing insights that would take humans hours or days to discover.

In this presentation, we covered three main topics: data processing, decision making, and customer interaction. We also discussed the implementation challenges and future opportunities in AI development.

The key takeaways are that AI is not just a trend, but a fundamental shift in how businesses operate. Companies that adopt AI early will have significant competitive advantages."""

    sample_summary = """**Video Summary**

This presentation focused on artificial intelligence in business applications. The main points covered were:

**Key Topics:**
- Data processing capabilities of AI
- AI-driven decision making
- Customer interaction improvements

**Main Benefits:**
- Rapid analysis of large datasets
- Insights generation in seconds vs hours
- Competitive advantages for early adopters

**Conclusion:**
AI represents a fundamental shift in business operations, not just a temporary trend. Early adoption provides significant competitive advantages."""

    return {
        "transcript": sample_transcript,
        "summary": sample_summary,
        "processing_time": 5.0,
        "video_duration": 180.0  # 3 minutes
    }

def upload_and_process_video(video_file) -> Optional[Dict[str, Any]]:
    """Upload video file to API and get processing results."""
    if DEMO_MODE:
        return simulate_video_processing(video_file)
    
    try:
        files = {"file": (video_file.name, video_file.read(), video_file.type)}
        
        with st.spinner("Processing video... This may take a few minutes."):
            response = requests.post(
                f"{API_BASE_URL}/upload-video",
                files=files,
                timeout=300  # 5 minutes timeout
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("Request timed out. The video might be too long or the server is busy.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
        return None

def main():
    """Main Streamlit application."""
    
    # Header
    st.title("🎥 Video Extractor")
    st.markdown("Upload a video to extract audio, generate transcripts, and create AI summaries")
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Instructions")
        if DEMO_MODE:
            st.info("🎭 **Demo Mode Active**")
            st.markdown("""
            This is a **demonstration version** of the Video Extractor app.
            
            1. **Upload** any video file to see the interface
            2. **Experience** the simulated processing workflow
            3. **Download** sample transcript and summary files
            
            **Demo Features:**
            - 🎵 Simulated audio extraction
            - 📝 Sample transcription output
            - 🤖 Example AI summary generation
            - 📄 Downloadable demo results
            
            *For full functionality with real video processing, deploy the complete application with FastAPI backend.*
            """)
        else:
            st.markdown("""
            1. **Upload** a video file (MP4, MOV, AVI, etc.)
            2. **Wait** for processing (may take several minutes)
            3. **Download** your transcript and summary files
            
            **Features:**
            - 🎵 Audio extraction from video
            - 📝 Speech-to-text transcription
            - 🤖 AI-powered summary generation
            - 📄 Downloadable results
            """)
        
        st.header("⚙️ Settings")
        
        # API Health Check
        if DEMO_MODE:
            st.warning("🎭 Demo Mode - API Not Required")
        elif check_api_health():
            st.success("✅ API Connected")
        else:
            st.error("❌ API Disconnected")
            st.warning("Make sure the FastAPI server is running on localhost:8000")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📁 Upload Video")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a video file",
            type=['mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm'],
            help="Supported formats: MP4, MOV, AVI, MKV, WMV, FLV, WebM"
        )
        
        if uploaded_file is not None:
            # Display video info
            st.subheader("📊 Video Information")
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / (1024*1024):.2f} MB",
                "File type": uploaded_file.type
            }
            
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                for key, value in list(file_details.items())[:2]:
                    st.metric(key, value)
            with col_info2:
                st.metric("File type", file_details["File type"])
            
            # Process button
            if st.button("🚀 Process Video", type="primary", use_container_width=True):
                # Reset file pointer
                uploaded_file.seek(0)
                
                # Process the video
                result = upload_and_process_video(uploaded_file)
                
                if result:
                    st.success("✅ Video processed successfully!")
                    
                    # Store results in session state
                    st.session_state['processing_result'] = result
                    st.session_state['video_name'] = Path(uploaded_file.name).stem
                    
                    # Trigger rerun to show results
                    st.rerun()
    
    with col2:
        st.header("📈 Processing Stats")
        
        if 'processing_result' in st.session_state:
            result = st.session_state['processing_result']
            
            # Display metrics
            st.metric("Video Duration", f"{result.get('video_duration', 0):.1f}s")
            st.metric("Processing Time", f"{result.get('processing_time', 0):.1f}s")
            
            # Progress indicator
            st.progress(1.0, "Complete")
        else:
            st.info("Upload a video to see processing statistics")
    
    # Results section
    if 'processing_result' in st.session_state:
        st.header("📋 Results")
        
        result = st.session_state['processing_result']
        video_name = st.session_state.get('video_name', 'video')
        
        # Create tabs for different outputs
        tab1, tab2, tab3 = st.tabs(["📝 Summary", "📄 Full Transcript", "💾 Downloads"])
        
        with tab1:
            st.subheader("🤖 AI-Generated Summary")
            summary = result.get('summary', 'No summary available')
            st.markdown(summary)
            
            # Copy button for summary
            if st.button("📋 Copy Summary", key="copy_summary"):
                st.write("Summary copied to clipboard!")  # Note: Actual clipboard copy requires additional setup
        
        with tab2:
            st.subheader("📝 Complete Transcript")
            transcript = result.get('transcript', 'No transcript available')
            
            # Show transcript in expandable section
            with st.expander("View Full Transcript", expanded=True):
                st.text_area(
                    "Transcript",
                    transcript,
                    height=400,
                    label_visibility="collapsed"
                )
        
        with tab3:
            st.subheader("💾 Download Files")
            
            col_dl1, col_dl2 = st.columns(2)
            
            with col_dl1:
                # Download transcript
                transcript_content = result.get('transcript', '')
                st.download_button(
                    label="📄 Download Transcript",
                    data=transcript_content,
                    file_name=f"{video_name}_transcript.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col_dl2:
                # Download summary
                summary_content = result.get('summary', '')
                st.download_button(
                    label="📝 Download Summary",
                    data=summary_content,
                    file_name=f"{video_name}_summary.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            # Download combined report
            combined_content = f"""# Video Analysis Report: {video_name}

## Summary
{summary_content}

## Full Transcript
{transcript_content}

---
Generated by Video Extractor
Processing Time: {result.get('processing_time', 0):.1f}s
Video Duration: {result.get('video_duration', 0):.1f}s
"""
            
            st.download_button(
                label="📊 Download Complete Report",
                data=combined_content,
                file_name=f"{video_name}_complete_report.md",
                mime="text/markdown",
                use_container_width=True
            )
    
    # Footer
    st.markdown("---")
    st.markdown(
        "Built with ❤️ using Streamlit and FastAPI | "
        "[GitHub Repository](https://github.com/jeff99jackson99/Videoextractor)"
    )

if __name__ == "__main__":
    main()
