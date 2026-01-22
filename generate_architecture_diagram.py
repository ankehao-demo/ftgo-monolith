#!/usr/bin/env python3
"""
FTGO Architecture Diagram Generator

This script generates an architecture diagram showing the current monolith state
and the target microservices architecture for the FTGO application migration.
"""

from graphviz import Digraph


def create_architecture_diagram():
    """Generate the FTGO architecture diagram showing current and target states."""
    
    dot = Digraph(comment='FTGO Architecture Migration', format='png')
    dot.attr(rankdir='TB', compound='true', fontname='Arial')
    dot.attr('node', fontname='Arial', fontsize='11')
    dot.attr('edge', fontname='Arial', fontsize='10')
    dot.attr(size='18,22', ratio='fill', dpi='150')
    dot.attr(nodesep='1.0', ranksep='1.2')
    
    # Title
    dot.attr(label='FTGO Monolith to Microservices Migration\n\n', labelloc='t', fontsize='18', fontname='Arial Bold')
    
    # ==================== CURRENT STATE (MONOLITH) ====================
    with dot.subgraph(name='cluster_current') as current:
        current.attr(label='Current State (Monolith)', style='rounded', bgcolor='#fff3e0', fontsize='14', fontname='Arial Bold')
        current.attr(margin='20')
        
        # Single Spring Boot Application
        with current.subgraph(name='cluster_monolith_app') as app:
            app.attr(label='FTGO Application\n(Single Spring Boot App)', style='rounded,filled', fillcolor='#e3f2fd', fontsize='12')
            app.attr(margin='15')
            
            # Services inside the monolith - arrange in a row (use non-cluster subgraph)
            with app.subgraph(name='mono_services_row') as mono_svcs:
                mono_svcs.attr(rank='same')
                mono_svcs.node('order_svc_mono', 'Order\nService', shape='box', style='rounded,filled', fillcolor='#bbdefb', width='1.3', height='0.8')
                mono_svcs.node('consumer_svc_mono', 'Consumer\nService', shape='box', style='rounded,filled', fillcolor='#bbdefb', width='1.3', height='0.8')
                mono_svcs.node('restaurant_svc_mono', 'Restaurant\nService', shape='box', style='rounded,filled', fillcolor='#bbdefb', width='1.3', height='0.8')
                mono_svcs.node('courier_svc_mono', 'Courier\nService', shape='box', style='rounded,filled', fillcolor='#bbdefb', width='1.3', height='0.8')
            
            # Show direct method calls within monolith (use xlabel for better label placement)
            app.edge('order_svc_mono', 'consumer_svc_mono', xlabel='direct call', style='dashed', color='#666666')
            app.edge('order_svc_mono', 'restaurant_svc_mono', xlabel='direct repo', style='dashed', color='#666666')
            app.edge('order_svc_mono', 'courier_svc_mono', style='dashed', color='#666666')
        
        # Shared Database
        current.node('shared_db', 'Shared MySQL\nDatabase\n(ftgo)', shape='cylinder', style='filled', fillcolor='#ffcc80', width='1.5', height='1')
        
        # All services connect to shared database
        current.edge('order_svc_mono', 'shared_db', label='@Transactional', color='#e65100')
        current.edge('consumer_svc_mono', 'shared_db', color='#e65100')
        current.edge('restaurant_svc_mono', 'shared_db', color='#e65100')
        current.edge('courier_svc_mono', 'shared_db', color='#e65100')
    
    # ==================== TARGET STATE (MICROSERVICES) ====================
    with dot.subgraph(name='cluster_target') as target:
        target.attr(label='Target State (Microservices)', style='rounded', bgcolor='#e8f5e9', fontsize='14', fontname='Arial Bold')
        target.attr(margin='25')
        
        # Top row: API Gateway and Service Registry (use non-cluster subgraph for layout)
        with target.subgraph(name='top_row') as top_row:
            top_row.attr(rank='same')
            top_row.node('api_gateway', 'API Gateway\n(Spring Cloud Gateway)', shape='box', style='rounded,filled', fillcolor='#c8e6c9', width='2.5', height='0.9')
            top_row.node('service_registry', 'Service Registry\n(Eureka/Consul)', shape='box', style='rounded,filled', fillcolor='#dcedc8', width='2.5', height='0.9')
        
        # Saga Orchestrator in its own row
        target.node('saga', 'Saga Orchestrator\n(Distributed Transactions)', shape='box', style='rounded,filled', fillcolor='#fff59d', width='3', height='0.9')
        
        # Services row (use non-cluster subgraph for layout)
        with target.subgraph(name='services_row') as svc_row:
            svc_row.attr(rank='same')
            svc_row.node('order_svc_ms', 'Order Service\n(Spring Boot)', shape='box', style='rounded,filled', fillcolor='#a5d6a7', width='1.8', height='0.9')
            svc_row.node('consumer_svc_ms', 'Consumer Service\n(Spring Boot)', shape='box', style='rounded,filled', fillcolor='#a5d6a7', width='1.8', height='0.9')
            svc_row.node('restaurant_svc_ms', 'Restaurant Service\n(Spring Boot)', shape='box', style='rounded,filled', fillcolor='#a5d6a7', width='1.8', height='0.9')
            svc_row.node('courier_svc_ms', 'Courier Service\n(Spring Boot)', shape='box', style='rounded,filled', fillcolor='#a5d6a7', width='1.8', height='0.9')
        
        # Databases row (use non-cluster subgraph for layout)
        with target.subgraph(name='db_row') as db_row:
            db_row.attr(rank='same')
            db_row.node('order_db', 'Order DB\n(MySQL)', shape='cylinder', style='filled', fillcolor='#81c784', width='1.2', height='0.8')
            db_row.node('consumer_db', 'Consumer DB\n(MySQL)', shape='cylinder', style='filled', fillcolor='#81c784', width='1.2', height='0.8')
            db_row.node('restaurant_db', 'Restaurant DB\n(MySQL)', shape='cylinder', style='filled', fillcolor='#81c784', width='1.2', height='0.8')
            db_row.node('courier_db', 'Courier DB\n(MySQL)', shape='cylinder', style='filled', fillcolor='#81c784', width='1.2', height='0.8')
        
        # API Gateway routes to services (green solid arrows)
        target.edge('api_gateway', 'order_svc_ms', color='#2e7d32', penwidth='1.5')
        target.edge('api_gateway', 'consumer_svc_ms', color='#2e7d32', penwidth='1.5')
        target.edge('api_gateway', 'restaurant_svc_ms', color='#2e7d32', penwidth='1.5')
        target.edge('api_gateway', 'courier_svc_ms', color='#2e7d32', penwidth='1.5')
        
        # Saga orchestrates distributed transactions (orange dashed arrows)
        target.edge('saga', 'order_svc_ms', style='dashed', color='#f57f17', penwidth='1.5')
        target.edge('saga', 'consumer_svc_ms', style='dashed', color='#f57f17', penwidth='1.5')
        target.edge('saga', 'restaurant_svc_ms', style='dashed', color='#f57f17', penwidth='1.5')
        target.edge('saga', 'courier_svc_ms', style='dashed', color='#f57f17', penwidth='1.5')
        
        # Services connect to their own databases (dark green arrows)
        target.edge('order_svc_ms', 'order_db', color='#1b5e20', penwidth='1.5')
        target.edge('consumer_svc_ms', 'consumer_db', color='#1b5e20', penwidth='1.5')
        target.edge('restaurant_svc_ms', 'restaurant_db', color='#1b5e20', penwidth='1.5')
        target.edge('courier_svc_ms', 'courier_db', color='#1b5e20', penwidth='1.5')
        
        # Services register with service registry (dotted arrows)
        target.edge('order_svc_ms', 'service_registry', style='dotted', color='#558b2f', penwidth='1.2', constraint='false')
        target.edge('consumer_svc_ms', 'service_registry', style='dotted', color='#558b2f', penwidth='1.2', constraint='false')
        target.edge('restaurant_svc_ms', 'service_registry', style='dotted', color='#558b2f', penwidth='1.2', constraint='false')
        target.edge('courier_svc_ms', 'service_registry', style='dotted', color='#558b2f', penwidth='1.2', constraint='false')
        
        # Inter-service communication via REST APIs (blue bold arrows)
        target.edge('order_svc_ms', 'consumer_svc_ms', style='bold', color='#0277bd', penwidth='2', constraint='false')
        target.edge('order_svc_ms', 'restaurant_svc_ms', style='bold', color='#0277bd', penwidth='2', constraint='false')
        target.edge('order_svc_ms', 'courier_svc_ms', style='bold', color='#0277bd', penwidth='2', constraint='false')
    
    # ==================== LEGEND ====================
    with dot.subgraph(name='cluster_legend') as legend:
        legend.attr(label='Legend', style='rounded', bgcolor='#fafafa', fontsize='14', fontname='Arial Bold')
        legend.attr(margin='20', rankdir='LR')
        
        # Create legend items with horizontal arrow examples using HTML-like labels
        # Each row has: start point -> end point (horizontal) + label
        
        # Row 1: Direct Method Call
        with legend.subgraph(name='leg_row1') as row1:
            row1.attr(rank='same')
            row1.node('leg1_start', '', shape='point', width='0.15', height='0.15')
            row1.node('leg1_end', '', shape='point', width='0.15', height='0.15')
            row1.node('leg1_label', 'Direct Method Call / Repository Access', shape='plaintext', fontsize='11')
        legend.edge('leg1_start', 'leg1_end', style='dashed', color='#666666', penwidth='2')
        legend.edge('leg1_end', 'leg1_label', style='invis')
        
        # Row 2: API Gateway to Service
        with legend.subgraph(name='leg_row2') as row2:
            row2.attr(rank='same')
            row2.node('leg2_start', '', shape='point', width='0.15', height='0.15')
            row2.node('leg2_end', '', shape='point', width='0.15', height='0.15')
            row2.node('leg2_label', 'API Gateway to Service (REST)', shape='plaintext', fontsize='11')
        legend.edge('leg2_start', 'leg2_end', color='#2e7d32', penwidth='2')
        legend.edge('leg2_end', 'leg2_label', style='invis')
        
        # Row 3: Inter-service REST API
        with legend.subgraph(name='leg_row3') as row3:
            row3.attr(rank='same')
            row3.node('leg3_start', '', shape='point', width='0.15', height='0.15')
            row3.node('leg3_end', '', shape='point', width='0.15', height='0.15')
            row3.node('leg3_label', 'Inter-Service REST API (Feign Client)', shape='plaintext', fontsize='11')
        legend.edge('leg3_start', 'leg3_end', style='bold', color='#0277bd', penwidth='2.5')
        legend.edge('leg3_end', 'leg3_label', style='invis')
        
        # Row 4: Database Connection
        with legend.subgraph(name='leg_row4') as row4:
            row4.attr(rank='same')
            row4.node('leg4_start', '', shape='point', width='0.15', height='0.15')
            row4.node('leg4_end', '', shape='point', width='0.15', height='0.15')
            row4.node('leg4_label', 'Database Connection', shape='plaintext', fontsize='11')
        legend.edge('leg4_start', 'leg4_end', color='#1b5e20', penwidth='2')
        legend.edge('leg4_end', 'leg4_label', style='invis')
        
        # Row 5: Service Registration
        with legend.subgraph(name='leg_row5') as row5:
            row5.attr(rank='same')
            row5.node('leg5_start', '', shape='point', width='0.15', height='0.15')
            row5.node('leg5_end', '', shape='point', width='0.15', height='0.15')
            row5.node('leg5_label', 'Service Registration', shape='plaintext', fontsize='11')
        legend.edge('leg5_start', 'leg5_end', style='dotted', color='#558b2f', penwidth='2')
        legend.edge('leg5_end', 'leg5_label', style='invis')
        
        # Row 6: Saga Coordination
        with legend.subgraph(name='leg_row6') as row6:
            row6.attr(rank='same')
            row6.node('leg6_start', '', shape='point', width='0.15', height='0.15')
            row6.node('leg6_end', '', shape='point', width='0.15', height='0.15')
            row6.node('leg6_label', 'Saga Coordination', shape='plaintext', fontsize='11')
        legend.edge('leg6_start', 'leg6_end', style='dashed', color='#f57f17', penwidth='2')
        legend.edge('leg6_end', 'leg6_label', style='invis')
        
        # Row 7: Shared Database Connection
        with legend.subgraph(name='leg_row7') as row7:
            row7.attr(rank='same')
            row7.node('leg7_start', '', shape='point', width='0.15', height='0.15')
            row7.node('leg7_end', '', shape='point', width='0.15', height='0.15')
            row7.node('leg7_label', 'Shared Database Connection', shape='plaintext', fontsize='11')
        legend.edge('leg7_start', 'leg7_end', color='#e65100', penwidth='2')
        legend.edge('leg7_end', 'leg7_label', style='invis')
        
        # Vertical ordering of rows
        legend.edge('leg1_start', 'leg2_start', style='invis')
        legend.edge('leg2_start', 'leg3_start', style='invis')
        legend.edge('leg3_start', 'leg4_start', style='invis')
        legend.edge('leg4_start', 'leg5_start', style='invis')
        legend.edge('leg5_start', 'leg6_start', style='invis')
        legend.edge('leg6_start', 'leg7_start', style='invis')
    
    # Migration arrow between states
    dot.edge('shared_db', 'api_gateway', label='  Migration  ', style='bold', color='#d32f2f', penwidth='2.5', arrowsize='1.5')
    
    return dot


def main():
    """Main function to generate and save the architecture diagram."""
    print("Generating FTGO Architecture Diagram...")
    
    diagram = create_architecture_diagram()
    
    # Render the diagram to PNG
    output_path = diagram.render('architecture_diagram', cleanup=True)
    print(f"Architecture diagram generated: {output_path}")
    
    # The render function adds the format extension, so we need to handle that
    # The output will be 'architecture_diagram.png'
    print("Done! The diagram has been saved as 'architecture_diagram.png'")


if __name__ == '__main__':
    main()
