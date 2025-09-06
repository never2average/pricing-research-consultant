import os
import json
from datetime import datetime
from typing import Any, Optional, List, Dict, Union
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY


def safe_str(value: Any) -> str:
    """Safely convert value to string"""
    if value is None:
        return "N/A"
    return str(value)


def format_json_content(data: Any, max_length: int = 500) -> str:
    """Format JSON data for PDF display"""
    if isinstance(data, dict):
        formatted = json.dumps(data, indent=2)
    elif isinstance(data, str):
        try:
            parsed = json.loads(data)
            formatted = json.dumps(parsed, indent=2)
        except:
            formatted = data
    else:
        formatted = str(data)
    
    # Truncate if too long
    if len(formatted) > max_length:
        formatted = formatted[:max_length] + "...\n[Content truncated]"
    
    return formatted


def create_section_header(title: str, styles: Dict[str, Any]) -> Any:
    """Create a section header"""
    return Paragraph(title, styles['section_header'])


def create_subsection_header(title: str, styles: Dict[str, Any]) -> Any:
    """Create a subsection header"""
    return Paragraph(title, styles['subsection_header'])


def create_content_paragraph(content: str, styles: Dict[str, Any]) -> Any:
    """Create a content paragraph with proper formatting"""
    if not content:
        content = "No data available"
    
    # Handle different content types
    if isinstance(content, dict) or isinstance(content, list):
        content = format_json_content(content)
    elif hasattr(content, 'model_dump'):
        content = format_json_content(content.model_dump())
    elif hasattr(content, 'dict'):
        content = format_json_content(content.dict())
    else:
        content = safe_str(content)
    
    return [Paragraph(content, styles['normal'])]


def create_pricing_table(pricing_response, styles):
    """Create a table for pricing recommendations"""
    if not pricing_response:
        return Paragraph("No pricing recommendations available", styles['normal'])
    
    elements = []
    
    # Main pricing info
    data = [
        ['Plan Name', safe_str(pricing_response.plan_name)],
        ['Unit Price', safe_str(pricing_response.unit_price)],
        ['Min Unit Count', safe_str(pricing_response.min_unit_count)],
        ['Unit Calculation Logic', safe_str(pricing_response.unit_calculation_logic)],
        ['Min Unit Utilization Period', safe_str(pricing_response.min_unit_utilization_period)]
    ]
    
    table = Table(data, colWidths=[2.5*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Customer segments
    if hasattr(pricing_response, 'recommended_customer_segment') and pricing_response.recommended_customer_segment:
        elements.append(Paragraph("Customer Segments:", styles['subsection_header']))
        elements.append(Spacer(1, 6))
        
        for idx, segment in enumerate(pricing_response.recommended_customer_segment, 1):
            elements.append(Paragraph(f"Segment {idx}:", styles['bold']))
            
            segment_data = [
                ['Existing Customer Segment', safe_str(segment.existing_customer_segment)],
                ['Customer Segment UID', safe_str(getattr(segment, 'customer_segment_uid', 'N/A'))],
                ['Customer Segment Name', safe_str(getattr(segment, 'customer_segment_name', 'N/A'))],
                ['Customer Segment Description', safe_str(getattr(segment, 'customer_segment_description', 'N/A'))]
            ]
            
            segment_table = Table(segment_data, colWidths=[2.5*inch, 4*inch])
            segment_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(segment_table)
            
            # Add projection table if available
            if hasattr(segment, 'projection') and segment.projection:
                elements.append(Spacer(1, 6))
                elements.append(Paragraph("Financial Projections:", styles['bold']))
                
                projection_data = [['Date', 'Revenue', 'Margin', 'Profit', 'Customer Count']]
                for fp in segment.projection:
                    projection_data.append([
                        safe_str(fp.date),
                        safe_str(fp.revenue),
                        safe_str(fp.margin),
                        safe_str(fp.profit),
                        safe_str(fp.customer_count)
                    ])
                
                proj_table = Table(projection_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
                proj_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(proj_table)
            
            elements.append(Spacer(1, 12))
    
    return elements


def generate_pdf_report(state: Any, output_path: Optional[str] = None) -> str:
    """Generate comprehensive PDF report from orchestration state"""
    
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"pricing_analysis_report_{timestamp}.pdf"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Create PDF document
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        'section_header',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.darkblue
    ))
    styles.add(ParagraphStyle(
        'subsection_header',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        textColor=colors.darkgreen
    ))
    styles.add(ParagraphStyle(
        'bold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        'normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        alignment=TA_JUSTIFY
    ))
    
    # Build PDF content
    content = []
    
    # Title page
    content.append(Paragraph("Pricing Research Analysis Report", styles['Title']))
    content.append(Spacer(1, 12))
    content.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    content.append(Paragraph(f"Invocation ID: {state.invocation_id}", styles['Normal']))
    content.append(Paragraph(f"Product ID: {state.product_id}", styles['Normal']))
    content.append(Spacer(1, 24))
    
    # Executive Summary
    content.append(create_section_header("Executive Summary", styles))
    summary_text = f"""
    This comprehensive pricing analysis report was generated through an orchestrated multi-step process involving 
    {len(state.get_completed_steps())} completed analysis steps out of {state.total_steps} total steps. 
    The analysis achieved {state.get_progress_percentage():.1f}% completion with {state.current_iteration} 
    iterations of refinement.
    """
    content.append(Paragraph(summary_text, styles['normal']))
    content.append(Spacer(1, 12))
    
    # Table of Contents
    content.append(create_section_header("Analysis Components", styles))
    completed_steps = state.get_completed_steps()
    for step in completed_steps:
        content.append(Paragraph(f"• {step.replace('_', ' ').title()}", styles['Normal']))
    content.append(PageBreak())
    
    # 1. Product Offering Analysis
    if hasattr(state, 'product_research') and state.product_research:
        content.append(create_section_header("1. Product Offering Analysis", styles))
        content.extend(create_content_paragraph(state.product_research, styles))
        content.append(Spacer(1, 12))
    
    # 2. Competitive Analysis
    if hasattr(state, 'competitive_analysis_research') and state.competitive_analysis_research:
        content.append(create_section_header("2. Competitive Analysis", styles))
        content.extend(create_content_paragraph(state.competitive_analysis_research, styles))
        content.append(Spacer(1, 12))
    
    # 3. Cashflow Analysis
    if hasattr(state, 'cashflow_analysis_research') and state.cashflow_analysis_research:
        content.append(create_section_header("3. Cashflow Analysis", styles))
        content.extend(create_content_paragraph(state.cashflow_analysis_research, styles))
        content.append(Spacer(1, 12))
    
    # 4. Segment-wise ROI Analysis
    if hasattr(state, 'segment_research') and state.segment_research:
        content.append(create_section_header("4. Segment-wise ROI Analysis", styles))
        content.extend(create_content_paragraph(state.segment_research, styles))
        content.append(Spacer(1, 12))
    
    # 5. Pricing Analysis
    if hasattr(state, 'pricing_research') and state.pricing_research:
        content.append(create_section_header("5. Pricing Analysis", styles))
        content.extend(create_content_paragraph(state.pricing_research, styles))
        content.append(Spacer(1, 12))
    
    # 6. Long-term Revenue Analysis
    if hasattr(state, 'longterm_revenue_research') and state.longterm_revenue_research:
        content.append(create_section_header("6. Long-term Revenue Analysis", styles))
        content.extend(create_content_paragraph(state.longterm_revenue_research, styles))
        content.append(Spacer(1, 12))
    
    # 7. Value Capture Analysis
    if hasattr(state, 'value_capture_research') and state.value_capture_research:
        content.append(create_section_header("7. Value Capture Analysis", styles))
        content.extend(create_content_paragraph(state.value_capture_research, styles))
        content.append(Spacer(1, 12))
    
    # 8. Experimental Pricing Recommendations
    if hasattr(state, 'experimental_pricing_research') and state.experimental_pricing_research:
        content.append(create_section_header("8. Experimental Pricing Recommendations", styles))
        content.extend(create_content_paragraph(state.experimental_pricing_research, styles))
        content.append(Spacer(1, 12))
    
    content.append(PageBreak())
    
    # 9. Final Pricing Recommendations (Structured)
    if hasattr(state, 'experimental_pricing_structured') and state.experimental_pricing_structured:
        content.append(create_section_header("9. Recommended Pricing Model", styles))
        pricing_elements = create_pricing_table(state.experimental_pricing_structured, styles)
        if isinstance(pricing_elements, list):
            content.extend(pricing_elements)
        else:
            content.append(pricing_elements)
        content.append(Spacer(1, 12))
    
    # 10. Iterative Refinement Results
    content.append(create_section_header("10. Iterative Refinement Analysis", styles))
    
    # Positioning Analysis
    if hasattr(state, 'positioning_analysis_research') and state.positioning_analysis_research:
        content.append(create_subsection_header("Positioning Analysis", styles))
        content.extend(create_content_paragraph(state.positioning_analysis_research, styles))
        content.append(Spacer(1, 8))
    
    # Persona Simulation
    if hasattr(state, 'persona_simulation_research') and state.persona_simulation_research:
        content.append(create_subsection_header("Persona-based Simulation", styles))
        content.extend(create_content_paragraph(state.persona_simulation_research, styles))
        content.append(Spacer(1, 8))
    
    # Cashflow Refinement
    if hasattr(state, 'cashflow_refinement_research') and state.cashflow_refinement_research:
        content.append(create_subsection_header("Cashflow Refinement", styles))
        content.extend(create_content_paragraph(state.cashflow_refinement_research, styles))
        content.append(Spacer(1, 8))
    
    # Analysis Metadata
    content.append(PageBreak())
    content.append(create_section_header("Analysis Metadata", styles))
    
    metadata_data = [
        ['Invocation ID', safe_str(state.invocation_id)],
        ['Product ID', safe_str(state.product_id)],
        ['Usage Scope', safe_str(getattr(state, 'usage_scope', 'N/A'))],
        ['Customer Segment ID', safe_str(getattr(state, 'customer_segment_id', 'N/A'))],
        ['Total Steps', safe_str(state.total_steps)],
        ['Completed Steps', safe_str(len(state.get_completed_steps()))],
        ['Progress Percentage', f"{state.get_progress_percentage():.1f}%"],
        ['Current Iteration', safe_str(state.current_iteration)],
        ['Max Iterations', safe_str(state.max_iterations)],
        ['Loop Completed', safe_str(getattr(state, 'loop_completed', False))],
        ['Pricing Model ID', safe_str(getattr(state, 'pricing_model_id', 'N/A'))],
        ['Recommended Pricing ID', safe_str(getattr(state, 'recommended_pricing_id', 'N/A'))]
    ]
    
    metadata_table = Table(metadata_data, colWidths=[3*inch, 3.5*inch])
    metadata_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    
    content.append(metadata_table)
    
    # Build PDF
    doc.build(content)
    print(f"PDF report generated: {output_path}")
    return output_path
