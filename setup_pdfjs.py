#!/usr/bin/env python
"""
Setup script to download and install PDF.js for the PaperLit application.
This script will download the PDF.js distribution and set it up in the static directory.
"""
import os
import sys
import shutil
import tempfile
import urllib.request
import zipfile

# PDF.js version to download
PDFJS_VERSION = "2.16.105"
PDFJS_URL = f"https://github.com/mozilla/pdf.js/releases/download/v{PDFJS_VERSION}/pdfjs-{PDFJS_VERSION}-dist.zip"

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(SCRIPT_DIR, "src", "static")
PDFJS_DIR = os.path.join(STATIC_DIR, "pdfjs")

# Custom highlight script
HIGHLIGHT_SCRIPT = """/**
 * Custom PDF.js extension for PaperLit to highlight text in PDFs
 */

// Store highlights
let currentHighlights = [];
let highlightColor = 'rgba(255, 255, 0, 0.3)';

// Function to find text in PDF pages
async function findTextInPDF(PDFViewerApplication, textToFind) {
  const highlights = [];
  const pdfDocument = PDFViewerApplication.pdfDocument;
  
  if (!pdfDocument) {
    console.error('PDF document not loaded');
    return highlights;
  }
  
  const numPages = pdfDocument.numPages;
  
  for (let pageNum = 1; pageNum <= numPages; pageNum++) {
    try {
      const page = await pdfDocument.getPage(pageNum);
      const textContent = await page.getTextContent();
      const textItems = textContent.items;
      
      // Simple text search (can be improved for better accuracy)
      const text = textItems.map(item => item.str).join(' ');
      
      let startIndex = 0;
      let index;
      
      // Find all occurrences of the text
      while ((index = text.indexOf(textToFind, startIndex)) !== -1) {
        // Find the text item that contains this text
        let charCount = 0;
        let startItem = -1;
        let endItem = -1;
        
        for (let i = 0; i < textItems.length; i++) {
          const itemLength = textItems[i].str.length;
          
          if (charCount <= index && index < charCount + itemLength) {
            startItem = i;
          }
          
          if (charCount <= index + textToFind.length && 
              index + textToFind.length <= charCount + itemLength) {
            endItem = i;
            break;
          }
          
          charCount += itemLength + 1; // +1 for the space we added when joining
        }
        
        if (startItem !== -1 && endItem !== -1) {
          highlights.push({
            pageNum,
            startItem,
            endItem,
            text: textToFind
          });
        }
        
        startIndex = index + textToFind.length;
      }
    } catch (error) {
      console.error(`Error processing page ${pageNum}:`, error);
    }
  }
  
  return highlights;
}

// Function to highlight text on PDF pages
function highlightTextOnPages(PDFViewerApplication, highlights, color) {
  // Clear existing highlights first
  clearHighlights(PDFViewerApplication);
  
  // Store the new highlights
  currentHighlights = highlights;
  highlightColor = color || 'rgba(255, 255, 0, 0.3)';
  
  // Apply highlights to visible pages
  applyHighlightsToVisiblePages(PDFViewerApplication);
}

// Function to apply highlights to currently visible pages
function applyHighlightsToVisiblePages(PDFViewerApplication) {
  const pdfViewer = PDFViewerApplication.pdfViewer;
  
  if (!pdfViewer) {
    console.error('PDF viewer not available');
    return;
  }
  
  const visiblePages = pdfViewer._getVisiblePages().views;
  
  for (const pageView of visiblePages) {
    const pageNumber = pageView.id;
    const pageHighlights = currentHighlights.filter(h => h.pageNum === pageNumber);
    
    if (pageHighlights.length > 0) {
      applyHighlightsToPage(pageView, pageHighlights);
    }
  }
}

// Function to apply highlights to a specific page
function applyHighlightsToPage(pageView, highlights) {
  const textLayer = pageView.textLayer;
  
  if (!textLayer || !textLayer.textContentItemsStr) {
    return; // Text layer not ready
  }
  
  const textItems = textLayer.textContentItemsStr;
  const textDivs = textLayer.textDivs;
  
  for (const highlight of highlights) {
    // Simple approach: highlight all divs between start and end
    for (let i = highlight.startItem; i <= highlight.endItem; i++) {
      if (i >= 0 && i < textDivs.length) {
        const div = textDivs[i];
        div.style.backgroundColor = highlightColor;
      }
    }
  }
}

// Function to clear all highlights
function clearHighlights(PDFViewerApplication) {
  const pdfViewer = PDFViewerApplication.pdfViewer;
  
  if (!pdfViewer) {
    return;
  }
  
  // Clear highlights from all pages
  for (let i = 0; i < pdfViewer._pages.length; i++) {
    const pageView = pdfViewer._pages[i];
    
    if (pageView && pageView.textLayer && pageView.textLayer.textDivs) {
      for (const div of pageView.textLayer.textDivs) {
        div.style.backgroundColor = '';
      }
    }
  }
  
  // Reset stored highlights
  currentHighlights = [];
}

// Initialize the extension when the document is loaded
document.addEventListener('webviewerloaded', function() {
  // Wait for the PDF viewer to initialize
  window.PDFViewerApplication.initializedPromise.then(() => {
    const PDFViewerApplication = window.PDFViewerApplication;
    
    // Notify the parent window that the PDF is loaded
    window.parent.postMessage({ type: 'PDF_LOADED' }, '*');
    
    // Listen for messages from the parent window
    window.addEventListener('message', async function(event) {
      if (!event.data || !event.data.type) return;
      
      switch (event.data.type) {
        case 'HIGHLIGHT_TEXT':
          if (event.data.blocks && Array.isArray(event.data.blocks)) {
            const highlights = [];
            
            // Process each block to find text in the PDF
            for (const block of event.data.blocks) {
              if (block.text) {
                const blockHighlights = await findTextInPDF(PDFViewerApplication, block.text);
                highlights.push(...blockHighlights);
              }
            }
            
            // Apply the highlights
            highlightTextOnPages(PDFViewerApplication, highlights, event.data.color);
          }
          break;
          
        case 'CLEAR_HIGHLIGHTS':
          clearHighlights(PDFViewerApplication);
          break;
      }
    });
    
    // Add event listener for page rendering to reapply highlights
    PDFViewerApplication.eventBus.on('pagerendered', function() {
      if (currentHighlights.length > 0) {
        applyHighlightsToVisiblePages(PDFViewerApplication);
      }
    });
  });
});
"""

def download_pdfjs():
    """Download and extract PDF.js to the static directory."""
    print(f"Downloading PDF.js v{PDFJS_VERSION}...")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Download the zip file
        zip_path = os.path.join(temp_dir, "pdfjs.zip")
        urllib.request.urlretrieve(PDFJS_URL, zip_path)
        
        # Extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Create the destination directory if it doesn't exist
        os.makedirs(STATIC_DIR, exist_ok=True)
        
        # Remove existing PDF.js directory if it exists
        if os.path.exists(PDFJS_DIR):
            shutil.rmtree(PDFJS_DIR)
        
        # Copy the extracted files to the static directory
        shutil.copytree(os.path.join(temp_dir, "build"), os.path.join(PDFJS_DIR, "build"))
        shutil.copytree(os.path.join(temp_dir, "web"), os.path.join(PDFJS_DIR, "web"))
        
        # Create the custom highlight script
        highlight_script_path = os.path.join(PDFJS_DIR, "web", "paperlit-highlight.js")
        with open(highlight_script_path, 'w') as f:
            f.write(HIGHLIGHT_SCRIPT)
        
        # Modify the viewer.html to include our custom script
        viewer_html_path = os.path.join(PDFJS_DIR, "web", "viewer.html")
        with open(viewer_html_path, 'r') as f:
            content = f.read()
        
        # Add our custom script after viewer.js
        content = content.replace('<script src="viewer.js"></script>', 
                                 '<script src="viewer.js"></script>\n  <script src="paperlit-highlight.js"></script>')
        
        with open(viewer_html_path, 'w') as f:
            f.write(content)
    
    print(f"PDF.js v{PDFJS_VERSION} has been successfully installed.")

if __name__ == "__main__":
    download_pdfjs()
