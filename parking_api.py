# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
import json
import os
import sys
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import traceback

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Database connection settings
def get_db_connection():
    """Establish database connection"""
    try:
        # Render platform provides DATABASE_URL environment variable
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            # Cloud environment (Render)
            print(f"Trying to connect to cloud database: {database_url[:20]}...") # Only show part of the connection string for security
            conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
            print("✓ Database connection successful")
            return conn
        else:
            # Local development using memory mode
            print("DATABASE_URL environment variable not found, using memory mode")
            return None
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("Using memory mode as backup")
        return None

# Memory data structure (for local development)
parking_data = {}

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    if not conn:
        print("Using memory mode")
        # Initialize memory data
        global parking_data
        for i in range(1, 5):
            parking_data[i] = {
                'id': i,
                'is_occupied': False,
                'plate_number': None,
                'started_at': None
            }
        return
    
    try:
        cursor = conn.cursor()
        # Create parking spaces table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parking_spaces (
                id INTEGER PRIMARY KEY,
                is_occupied BOOLEAN DEFAULT FALSE,
                license_plate_number VARCHAR(20),
                license_plate_color VARCHAR(20),
                parking_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Default create 4 parking spaces
        for i in range(1, 5):
            cursor.execute("""
                INSERT INTO parking_spaces (id, is_occupied, license_plate_number, license_plate_color) 
                VALUES (%s, %s, %s, %s) 
                ON CONFLICT (id) DO NOTHING;
            """, (i, False, None, None))
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✓ Database initialization complete")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        print(f"Error details: {traceback.format_exc()}")
        print("Using memory mode as backup")

# Initialize database on application startup
init_database()

def calculate_fee(start_time):
    """Calculate parking fee, first 30 minutes free, then $20 per hour"""
    if not start_time:
        return 0
    
    current_time = datetime.now()
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time.replace('T', ' '))
    
    duration = current_time - start_time
    duration_minutes = int(duration.total_seconds() / 60)
    
    if duration_minutes <= 30:
        return 0
    else:
        # After 30 minutes, $20 per hour
        billable_minutes = duration_minutes - 30
        hours = (billable_minutes + 59) // 60  # Round up to the next hour
        return hours * 20

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        'message': 'Parking Management API Service',
        'version': '1.0.0',
        'endpoints': [
            'POST /api/parking/update - Update parking space status',
            'GET /api/parking/status - Query all parking spaces',
            'GET /api/parking/my_status?plate=LICENSE - Query individual parking status'
        ],
        'status': 'running',
        'current_time': datetime.now().isoformat(),
        'active_parkings': len(parking_data)
    })

@app.route('/api/parking/update', methods=['POST'])
def update_parking_status():
    """Receive parking space status from Raspberry Pi"""
    try:
        data = request.get_json()
        
        if not data or not isinstance(data, list) or len(data) != 4:
            return jsonify({
                'success': False,
                'error': 'Invalid data format, must include status data for 4 parking spaces'
            }), 400
        
        current_time = datetime.now()
        conn = get_db_connection()
        
        if conn:
            # Using database
            try:
                cursor = conn.cursor()
                
                # Ensure table exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS parking_spaces (
                        id INTEGER PRIMARY KEY,
                        is_occupied BOOLEAN DEFAULT FALSE,
                        license_plate_number VARCHAR(20),
                        license_plate_color VARCHAR(20),
                        parking_time TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
                
                for space_data in data:
                    space_id = space_data.get('ID')
                    is_occupied = space_data.get('IsOccupied', False)
                    plate_number = space_data.get('LicensePlateNumber', 'None')
                    plate_color = space_data.get('LicensePlateColor', 'None')
                    
                    # Handle empty values
                    if plate_number == 'None' or not plate_number:
                        plate_number = None
                    if plate_color == 'None' or not plate_color:
                        plate_color = None
                    
                    # Check if parking space exists
                    cursor.execute("SELECT COUNT(*) FROM parking_spaces WHERE id = %s", (space_id,))
                    if cursor.fetchone()['count'] == 0:
                        # If it doesn't exist, create it
                        cursor.execute("""
                            INSERT INTO parking_spaces 
                            (id, is_occupied, license_plate_number, license_plate_color, parking_time, created_at, updated_at) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (space_id, is_occupied, plate_number, plate_color, 
                              current_time if is_occupied else None, current_time, current_time))
                    else:
                        # Update existing parking space
                        cursor.execute("""
                            UPDATE parking_spaces 
                            SET is_occupied = %s, 
                                license_plate_number = %s,
                                license_plate_color = %s,
                                parking_time = %s,
                                updated_at = %s
                            WHERE id = %s;
                        """, (is_occupied, plate_number, plate_color, 
                              current_time if is_occupied else None, current_time, space_id))
                
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"✗ Database update failed: {e}")
                print(f"Error details: {traceback.format_exc()}")
                conn.close()
                raise e
        else:
            # Using memory mode (local development)
            for space_data in data:
                space_id = space_data.get('ID')
                is_occupied = space_data.get('IsOccupied', False)
                plate_number = space_data.get('LicensePlateNumber', 'None')
                
                # Validate space ID
                if space_id not in [1, 2, 3, 4]:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid parking space ID: {space_id}'
                    }), 400
                
                # Handle empty values
                if plate_number == 'None' or not plate_number:
                    plate_number = None
                
                # Memory data mode
                if is_occupied:
                    parking_data[space_id] = {
                        'id': space_id,
                        'plate_number': plate_number,
                        'started_at': current_time,
                        'is_occupied': True
                    }
                else:
                    # If space is vacated, remove license plate info or mark as empty
                    if space_id in parking_data:
                        parking_data[space_id]['is_occupied'] = False
                        parking_data[space_id]['plate_number'] = None
        
        return jsonify({
            'success': True,
            'message': 'Parking space status updated successfully',
            'timestamp': current_time.isoformat(),
            'storage_mode': 'database' if conn else 'memory'
        })
        
    except Exception as e:
        print(f"✗ Error processing parking status request: {e}")
        print(f"Error details: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Update failed: {str(e)}'
        }), 500

@app.route('/api/parking/status', methods=['GET'])
def get_parking_status():
    """Query all parking spaces"""
    try:
        conn = get_db_connection()
        
        if conn:
            # Using database
            try:
                cursor = conn.cursor()
                
                # Ensure table exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS parking_spaces (
                        id INTEGER PRIMARY KEY,
                        is_occupied BOOLEAN DEFAULT FALSE,
                        license_plate_number VARCHAR(20),
                        license_plate_color VARCHAR(20),
                        parking_time TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Default create 4 parking spaces
                for i in range(1, 5):
                    cursor.execute("""
                        INSERT INTO parking_spaces (id, is_occupied, license_plate_number, license_plate_color) 
                        VALUES (%s, %s, %s, %s) 
                        ON CONFLICT (id) DO NOTHING;
                    """, (i, False, None, None))
                
                conn.commit()
                
                cursor.execute("SELECT * FROM parking_spaces ORDER BY id;")
                spaces = cursor.fetchall()
                cursor.close()
                conn.close()
                
                result = []
                for space in spaces:
                    result.append({
                        'id': space['id'],
                        'is_occupied': space['is_occupied'],
                        'plate_number': space['license_plate_number']
                    })
                return jsonify(result)
            except Exception as e:
                print(f"✗ Database query failed: {e}")
                print(f"Error details: {traceback.format_exc()}")
                conn.close()
                raise e
        else:
            # Using memory mode (local development)
            result = []
            for space_id in range(1, 5):
                if space_id in parking_data and parking_data[space_id]['is_occupied']:
                    result.append({
                        'id': space_id,
                        'is_occupied': True,
                        'plate_number': parking_data[space_id]['plate_number']
                    })
                else:
                    result.append({
                        'id': space_id,
                        'is_occupied': False,
                        'plate_number': None
                    })
            return jsonify(result)
        
    except Exception as e:
        print(f"✗ Error processing query request: {e}")
        print(f"Error details: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Query failed: {str(e)}'
        }), 500

@app.route('/api/parking/my_status', methods=['GET'])
def get_my_parking_status():
    """Query individual parking status"""
    try:
        plate = request.args.get('plate')
        
        if not plate:
            return jsonify({
                'success': False,
                'error': 'License plate number is required'
            }), 400
        
        conn = get_db_connection()
        
        if conn:
            # Using database
            try:
                cursor = conn.cursor()
                
                # Ensure table exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS parking_spaces (
                        id INTEGER PRIMARY KEY,
                        is_occupied BOOLEAN DEFAULT FALSE,
                        license_plate_number VARCHAR(20),
                        license_plate_color VARCHAR(20),
                        parking_time TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
                
                cursor.execute("SELECT * FROM parking_spaces WHERE license_plate_number = %s;", (plate,))
                space = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if space and space['is_occupied']:
                    start_time = space['parking_time']
                    if start_time:
                        current_time = datetime.now()
                        
                        # Calculate parking duration
                        duration = current_time - start_time
                        duration_minutes = int(duration.total_seconds() / 60)
                        
                        # Calculate parking fee
                        fee = calculate_fee(start_time)
                        
                        return jsonify({
                            'is_parked': True,
                            'parking_slot': space['id'],
                            'started_at': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'duration_minutes': duration_minutes,
                            'fee': fee
                        })
            except Exception as e:
                print(f"✗ Database query failed: {e}")
                print(f"Error details: {traceback.format_exc()}")
                conn.close()
                raise e
        else:
            # Using memory mode (local development)
            for space_id, space in parking_data.items():
                if space['is_occupied'] and space['plate_number'] == plate:
                    start_time = space['started_at']
                    current_time = datetime.now()
                    
                    # Calculate parking duration
                    duration = current_time - start_time
                    duration_minutes = int(duration.total_seconds() / 60)
                    
                    # Calculate parking fee
                    fee = calculate_fee(start_time)
                    
                    return jsonify({
                        'is_parked': True,
                        'parking_slot': space_id,
                        'started_at': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'duration_minutes': duration_minutes,
                        'fee': fee
                    })
        
        # Parking space not occupied
        return jsonify({
            'is_parked': False,
            'message': 'No parking space occupied by this license plate'
        })
        
    except Exception as e:
        print(f"✗ Error processing query request: {e}")
        print(f"Error details: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Query failed: {str(e)}'
        }), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint, for Render platform to check database connection"""
    try:
        # Check database connection
        conn = get_db_connection()
        db_status = "connected" if conn else "disconnected"
        if conn:
            conn.close()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime': 'running',
            'database': db_status
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'API endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # For local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)