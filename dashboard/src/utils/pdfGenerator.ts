import { jsPDF } from 'jspdf';
import React from 'react';

export interface ChatMessage {
  role: 'user' | 'agent';
  content: string;
}

interface GeneratePDFOptions {
  messages: ChatMessage[];
  agentMode: 'Single Agent' | 'Multi-Agent';
  onProgress: (percent: number) => void;
  abortRef: React.MutableRefObject<boolean>;
}

interface RenderLine {
  text: string;
  font: 'helvetica' | 'courier';
  style: 'normal' | 'bold';
  size: number;
  textColor: number[];
}

export const generatePDF = async ({ messages, agentMode, onProgress, abortRef }: GeneratePDFOptions) => {
  const doc = new jsPDF({ format: 'a4', unit: 'mm' });
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  
  const margin = 15;
  const topMargin = 20;
  const bottomMargin = 20;
  const bubbleMaxWidth = 140; 
  const padding = 5;
  
  let currentY = topMargin;
  let currentPage = 1;

  const drawFooter = () => {
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.setTextColor(150);
    doc.text(`Page ${currentPage}`, pageWidth / 2, pageHeight - 10, { align: 'center' });
  };

  // 1. Draw First Page Header
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(18);
  doc.setTextColor(40);
  doc.text('Financial Intelligence Report', margin, currentY);
  currentY += 8;

  doc.setDrawColor(200);
  doc.setLineWidth(0.5);
  doc.line(margin, currentY, pageWidth - margin, currentY);
  currentY += 8;

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(12);
  doc.setTextColor(100);
  doc.text(`Agent Mode : ${agentMode}`, margin, currentY);
  currentY += 6;
  const dateStr = new Date().toLocaleString('en-US', { dateStyle: 'long', timeStyle: 'short' });
  doc.text(`Generated  : ${dateStr}`, margin, currentY);
  currentY += 6;
  doc.text(`Messages   : ${messages.length}`, margin, currentY);
  currentY += 15;

  // 2. Process Messages
  for (let i = 0; i < messages.length; i++) {
    if (abortRef.current) {
      console.log('PDF Generation aborted by user.');
      return;
    }

    const msg = messages[i];
    const isUser = msg.role === 'user';
    
    // Parse Markdown roughly
    const rawLines = msg.content.split('\n');
    const parsedLines: RenderLine[] = [];
    
    let inCodeBlock = false;
    
    for (const line of rawLines) {
      if (line.trim().startsWith('```')) {
        inCodeBlock = !inCodeBlock;
        continue;
      }
      
      let text = line;
      // Strip inline bold for simplified native rendering
      text = text.replace(/\*\*(.*?)\*\*/g, '$1').replace(/__(.*?)__/g, '$1');
      
      let font: 'helvetica' | 'courier' = inCodeBlock ? 'courier' : 'helvetica';
      let style: 'normal' | 'bold' = 'normal';
      let size = 11;
      let textColor = isUser ? [20, 20, 20] : [40, 40, 40];

      if (!inCodeBlock) {
        if (text.startsWith('# ')) {
          style = 'bold'; size = 16; text = text.replace('# ', '');
        } else if (text.startsWith('## ')) {
          style = 'bold'; size = 14; text = text.replace('## ', '');
        } else if (text.startsWith('### ')) {
          style = 'bold'; size = 12; text = text.replace('### ', '');
        } else if (text.startsWith('- ') || text.startsWith('* ')) {
          text = '  • ' + text.substring(2);
        }
      } else {
        textColor = [60, 60, 60];
      }
      
      // Calculate wrapping for this specific line
      doc.setFont(font, style);
      doc.setFontSize(size);
      const wrapped = doc.splitTextToSize(text, bubbleMaxWidth - padding * 2);
      
      for (const wLine of wrapped) {
        parsedLines.push({ text: wLine, font, style, size, textColor });
      }
    }
    
    // Segment the message into chunks that fit on the current page
    let linesRemaining = [...parsedLines];

    while (linesRemaining.length > 0) {
      if (abortRef.current) {
        console.log('PDF Generation aborted by user.');
        return;
      }

      let spaceLeft = pageHeight - bottomMargin - currentY - (padding * 2);

      // If less than 15mm left (approx 3 lines), break to new page early to avoid awkward tiny slices
      if (spaceLeft < 15) {
        drawFooter();
        doc.addPage();
        currentPage++;
        currentY = topMargin;
        spaceLeft = pageHeight - bottomMargin - currentY - (padding * 2);
      }

      const linesForThisPage = [];
      let heightForThisPage = 0;

      for (const line of linesRemaining) {
        const lh = (line.size * 0.35) * 1.5;
        // Always push at least one line to prevent infinite loops if a line is weirdly tall
        if (heightForThisPage === 0 || heightForThisPage + lh <= spaceLeft) {
          linesForThisPage.push(line);
          heightForThisPage += lh;
        } else {
          break;
        }
      }

      linesRemaining = linesRemaining.slice(linesForThisPage.length);

      // Draw Segment Bubble
      const totalBubbleHeight = heightForThisPage + (padding * 2);
      const bubbleX = isUser ? pageWidth - margin - bubbleMaxWidth : margin;

      if (isUser) {
        doc.setFillColor(219, 234, 254);
        doc.setDrawColor(191, 219, 254);
      } else {
        doc.setFillColor(243, 244, 246);
        doc.setDrawColor(229, 231, 235);
      }

      doc.roundedRect(bubbleX, currentY, bubbleMaxWidth, totalBubbleHeight, 3, 3, 'FD');

      // Draw Text for this segment
      let textY = currentY + padding + 4;
      for (const pline of linesForThisPage) {
        doc.setFont(pline.font, pline.style);
        doc.setFontSize(pline.size);
        doc.setTextColor(pline.textColor[0], pline.textColor[1], pline.textColor[2]);
        const textX = bubbleX + padding;
        doc.text(pline.text, textX, textY);
        textY += (pline.size * 0.35) * 1.5;
      }

      currentY += totalBubbleHeight + 6;

      // Force a page break if there are still lines left for this message
      if (linesRemaining.length > 0) {
        drawFooter();
        doc.addPage();
        currentPage++;
        currentY = topMargin;
      }
    }

    // Report Progress
    const percent = Math.round(((i + 1) / messages.length) * 100);
    onProgress(percent);

    // Yield to browser event loop
    await new Promise(resolve => requestAnimationFrame(resolve));
  }

  // Draw final footer
  drawFooter();

  // Save
  const safeDate = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 16);
  doc.save(`Financial_Report_${safeDate}.pdf`);
};
