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
    
    # Title
    dot.attr(label='FTGO Monolith to Microservices Migration\n\n', labelloc='t', fontsize='16', fontname='Arial Bold')
    
    # ==================== CURRENT STATE (MONOLITH) ====================
    with dot.subgraph(name='cluster_current') as current:
        current.attr(label='Current State (Monolith)', style='rounded', bgcolor='#fff3e0', fontsize='14', fontname='Arial Bold')
        
        # Single Spring Boot Application
        with current.subgraph(name='cluster_monolith_app') as app:
            app.attr(label='FTGO Application\n(Single Spring Boot App)', style='rounded,filled', fillcolor='#e3f2fd', fontsize='12')
            
            # Services inside the monolith
            app.node('order_svc_mono', 'Order\nService', shape='box', style='rounded,filled', fillcolor='#bbdefb')
            app.node('consumer_svc_mono', 'Consumer\nService', shape='box', style='rounded,filled', fillcolor='#bbdefb')
            app.node('restaurant_svc_mono', 'Restaurant\nService', shape='box', style='rounded,filled', fillcolor='#bbdefb')
            app.node('courier_svc_mono', 'Courier\nService', shape='box', style='rounded,filled', fillcolor='#bbdefb')
            
            # Show direct method calls within monolith
            app.edge('order_svc_mono', 'consumer_svc_mono', label='direct call', style='dashed', color='#666666')
            app.edge('order_svc_mono', 'restaurant_svc_mono', label='direct\nrepository\naccess', style='dashed', color='#666666')
            app.edge('order_svc_mono', 'courier_svc_mono', label='direct\nrepository\naccess', style='dashed', color='#666666')
        
        # Shared Database
        current.node('shared_db', 'Shared MySQL\nDatabase\n(ftgo)', shape='cylinder', style='filled', fillcolor='#ffcc80')
        
        # All services connect to shared database
        current.edge('order_svc_mono', 'shared_db', label='@Transactional', color='#e65100')
        current.edge('consumer_svc_mono', 'shared_db', color='#e65100')
        current.edge('restaurant_svc_mono', 'shared_db', color='#e65100')
        current.edge('courier_svc_mono', 'shared_db', color='#e65100')
    
    # ==================== TARGET STATE (MICROSERVICES) ====================
    with dot.subgraph(name='cluster_target') as target:
        target.attr(label='Target State (Microservices)', style='rounded', bgcolor='#e8f5e9', fontsize='14', fontname='Arial Bold')
        
        # API Gateway
        target.node('api_gateway', 'API Gateway\n(Spring Cloud Gateway)', shape='box', style='rounded,filled', fillcolor='#c8e6c9', width='2')
        
        # Service Registry
        target.node('service_registry', 'Service Registry\n(Eureka/Consul)', shape='box', style='rounded,filled', fillcolor='#dcedc8', width='2')
        
        # Individual Microservices
        with target.subgraph(name='cluster_order_ms') as order_ms:
            order_ms.attr(label='', style='invis')
            order_ms.node('order_svc_ms', 'Order Service\n(Spring Boot)', shape='box', style='rounded,filled', fillcolor='#a5d6a7')
            order_ms.node('order_db', 'Order DB\n(MySQL)', shape='cylinder', style='filled', fillcolor='#81c784')
        
        with target.subgraph(name='cluster_consumer_ms') as consumer_ms:
            consumer_ms.attr(label='', style='invis')
            consumer_ms.node('consumer_svc_ms', 'Consumer Service\n(Spring Boot)', shape='box', style='rounded,filled', fillcolor='#a5d6a7')
            consumer_ms.node('consumer_db', 'Consumer DB\n(MySQL)', shape='cylinder', style='filled', fillcolor='#81c784')
        
        with target.subgraph(name='cluster_restaurant_ms') as restaurant_ms:
            restaurant_ms.attr(label='', style='invis')
            restaurant_ms.node('restaurant_svc_ms', 'Restaurant Service\n(Spring Boot)', shape='box', style='rounded,filled', fillcolor='#a5d6a7')
            restaurant_ms.node('restaurant_db', 'Restaurant DB\n(MySQL)', shape='cylinder', style='filled', fillcolor='#81c784')
        
        with target.subgraph(name='cluster_courier_ms') as courier_ms:
            courier_ms.attr(label='', style='invis')
            courier_ms.node('courier_svc_ms', 'Courier Service\n(Spring Boot)', shape='box', style='rounded,filled', fillcolor='#a5d6a7')
            courier_ms.node('courier_db', 'Courier DB\n(MySQL)', shape='cylinder', style='filled', fillcolor='#81c784')
        
        # Saga Orchestrator
        target.node('saga', 'Saga Orchestrator\n(Distributed Transactions)', shape='box', style='rounded,filled', fillcolor='#fff59d', width='2')
        
        # API Gateway routes to services
        target.edge('api_gateway', 'order_svc_ms', label='REST API', color='#2e7d32')
        target.edge('api_gateway', 'consumer_svc_ms', label='REST API', color='#2e7d32')
        target.edge('api_gateway', 'restaurant_svc_ms', label='REST API', color='#2e7d32')
        target.edge('api_gateway', 'courier_svc_ms', label='REST API', color='#2e7d32')
        
        # Services register with service registry
        target.edge('order_svc_ms', 'service_registry', style='dotted', color='#558b2f', constraint='false')
        target.edge('consumer_svc_ms', 'service_registry', style='dotted', color='#558b2f', constraint='false')
        target.edge('restaurant_svc_ms', 'service_registry', style='dotted', color='#558b2f', constraint='false')
        target.edge('courier_svc_ms', 'service_registry', style='dotted', color='#558b2f', constraint='false')
        
        # Services connect to their own databases
        target.edge('order_svc_ms', 'order_db', color='#1b5e20')
        target.edge('consumer_svc_ms', 'consumer_db', color='#1b5e20')
        target.edge('restaurant_svc_ms', 'restaurant_db', color='#1b5e20')
        target.edge('courier_svc_ms', 'courier_db', color='#1b5e20')
        
        # Saga orchestrates distributed transactions
        target.edge('saga', 'order_svc_ms', label='Saga\nPattern', style='dashed', color='#f57f17')
        target.edge('saga', 'consumer_svc_ms', style='dashed', color='#f57f17')
        target.edge('saga', 'restaurant_svc_ms', style='dashed', color='#f57f17')
        target.edge('saga', 'courier_svc_ms', style='dashed', color='#f57f17')
        
        # Inter-service communication via REST APIs
        target.edge('order_svc_ms', 'consumer_svc_ms', label='REST API\n(Feign Client)', style='bold', color='#0277bd', constraint='false')
        target.edge('order_svc_ms', 'restaurant_svc_ms', label='REST API', style='bold', color='#0277bd', constraint='false')
        target.edge('order_svc_ms', 'courier_svc_ms', label='REST API', style='bold', color='#0277bd', constraint='false')
    
    # ==================== LEGEND ====================
    with dot.subgraph(name='cluster_legend') as legend:
        legend.attr(label='Legend', style='rounded', bgcolor='#fafafa', fontsize='12')
        legend.node('leg1', 'Direct Method Call / Repository Access', shape='plaintext', fontsize='10')
        legend.node('leg2', 'REST API Communication', shape='plaintext', fontsize='10')
        legend.node('leg3', 'Database Connection', shape='plaintext', fontsize='10')
        legend.node('leg4', 'Service Registration', shape='plaintext', fontsize='10')
        legend.node('leg5', 'Saga Coordination', shape='plaintext', fontsize='10')
        
        legend.edge('leg1', 'leg2', style='invis')
        legend.edge('leg2', 'leg3', style='invis')
        legend.edge('leg3', 'leg4', style='invis')
        legend.edge('leg4', 'leg5', style='invis')
    
    # Migration arrow between states
    dot.edge('shared_db', 'api_gateway', label='  Migration  ', style='bold', color='#d32f2f', penwidth='2', arrowsize='1.5')
    
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
