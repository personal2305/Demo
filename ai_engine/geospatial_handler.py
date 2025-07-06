import re
import json
import logging
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.ops import transform
import folium
from datetime import datetime

logger = logging.getLogger(__name__)

class GeospatialHandler:
    """Handler for geospatial queries and spatial data processing"""
    
    def __init__(self):
        self.coordinate_patterns = self._setup_coordinate_patterns()
        self.location_cache = {}
        self.india_bounds = {
            'min_lat': 6.4627,
            'max_lat': 37.6,
            'min_lon': 68.1766,
            'max_lon': 97.4025
        }
        
    def _setup_coordinate_patterns(self) -> List[Dict[str, str]]:
        """Setup regex patterns for coordinate extraction"""
        return [
            {
                'name': 'decimal_degrees',
                'pattern': r'(-?\d+\.?\d*)\s*[,°]\s*(-?\d+\.?\d*)',
                'description': 'Decimal degrees format (lat, lon)'
            },
            {
                'name': 'dms_format',
                'pattern': r'(\d+)°\s*(\d+)′\s*(\d+\.?\d*)″\s*([NSEW])',
                'description': 'Degrees, minutes, seconds format'
            },
            {
                'name': 'coordinate_with_direction',
                'pattern': r'(\d+\.?\d*)\s*([NSEW])\s*(\d+\.?\d*)\s*([NSEW])',
                'description': 'Coordinates with cardinal directions'
            }
        ]
    
    def extract_coordinates(self, text: str) -> List[Dict[str, Any]]:
        """Extract coordinate information from text"""
        coordinates = []
        
        try:
            for pattern_info in self.coordinate_patterns:
                pattern = pattern_info['pattern']
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    coord_info = self._parse_coordinate_match(match, pattern_info)
                    if coord_info and self._validate_coordinates(coord_info['lat'], coord_info['lon']):
                        coordinates.append(coord_info)
            
            # Remove duplicates
            unique_coords = []
            for coord in coordinates:
                is_duplicate = False
                for existing in unique_coords:
                    if (abs(existing['lat'] - coord['lat']) < 0.001 and 
                        abs(existing['lon'] - coord['lon']) < 0.001):
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_coords.append(coord)
            
            return unique_coords
            
        except Exception as e:
            logger.error(f"Error extracting coordinates: {str(e)}")
            return []
    
    def _parse_coordinate_match(self, match, pattern_info: Dict) -> Optional[Dict[str, Any]]:
        """Parse a coordinate match based on the pattern type"""
        try:
            if pattern_info['name'] == 'decimal_degrees':
                lat, lon = float(match.group(1)), float(match.group(2))
                return {
                    'lat': lat,
                    'lon': lon,
                    'format': 'decimal_degrees',
                    'raw_text': match.group(0),
                    'confidence': 0.9
                }
            
            elif pattern_info['name'] == 'dms_format':
                # Convert DMS to decimal degrees
                degrees = float(match.group(1))
                minutes = float(match.group(2))
                seconds = float(match.group(3))
                direction = match.group(4).upper()
                
                decimal = degrees + minutes/60 + seconds/3600
                if direction in ['S', 'W']:
                    decimal = -decimal
                
                # This is a simplified version - would need more logic to determine lat/lon
                return {
                    'lat': decimal if direction in ['N', 'S'] else 0,
                    'lon': decimal if direction in ['E', 'W'] else 0,
                    'format': 'dms',
                    'raw_text': match.group(0),
                    'confidence': 0.8
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing coordinate match: {str(e)}")
            return None
    
    def _validate_coordinates(self, lat: float, lon: float) -> bool:
        """Validate if coordinates are reasonable"""
        return (-90 <= lat <= 90) and (-180 <= lon <= 180)
    
    def extract_location_names(self, text: str) -> List[Dict[str, Any]]:
        """Extract location names from text"""
        locations = []
        
        # Common Indian location patterns
        location_patterns = [
            r'\b(delhi|mumbai|kolkata|chennai|bangalore|hyderabad|pune|ahmedabad)\b',
            r'\b(maharashtra|karnataka|tamil nadu|rajasthan|uttar pradesh|gujarat)\b',
            r'\b(india|indian ocean|arabian sea|bay of bengal)\b',
            r'\b(\w+)\s+(district|state|city|region|area)\b',
            r'\b(north|south|east|west|central)\s+(india|indian)\b'
        ]
        
        try:
            for pattern in location_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    location_text = match.group(0).strip()
                    locations.append({
                        'name': location_text,
                        'type': 'location',
                        'raw_text': location_text,
                        'confidence': 0.7,
                        'bounds': self._get_location_bounds(location_text)
                    })
            
            return locations
            
        except Exception as e:
            logger.error(f"Error extracting location names: {str(e)}")
            return []
    
    def _get_location_bounds(self, location_name: str) -> Optional[Dict[str, float]]:
        """Get approximate bounds for a location (simplified version)"""
        # This would ideally connect to a geocoding service
        # For now, return India bounds for any location
        location_lower = location_name.lower()
        
        known_locations = {
            'india': self.india_bounds,
            'delhi': {'min_lat': 28.4, 'max_lat': 28.9, 'min_lon': 76.8, 'max_lon': 77.5},
            'mumbai': {'min_lat': 18.9, 'max_lat': 19.3, 'min_lon': 72.7, 'max_lon': 73.0},
            'bangalore': {'min_lat': 12.8, 'max_lat': 13.2, 'min_lon': 77.4, 'max_lon': 77.8}
        }
        
        for known_loc, bounds in known_locations.items():
            if known_loc in location_lower:
                return bounds
        
        return None
    
    def process_geospatial_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a geospatial query and return relevant spatial information"""
        try:
            query_text = query_data.get('cleaned_query', '')
            
            # Extract spatial elements
            coordinates = self.extract_coordinates(query_text)
            locations = self.extract_location_names(query_text)
            
            # Determine spatial intent
            spatial_intent = self._classify_spatial_intent(query_text)
            
            # Generate spatial suggestions
            suggestions = self._generate_spatial_suggestions(coordinates, locations, spatial_intent)
            
            # Create map if coordinates or locations found
            map_data = None
            if coordinates or locations:
                map_data = self._create_interactive_map(coordinates, locations)
            
            return {
                'coordinates': coordinates,
                'locations': locations,
                'spatial_intent': spatial_intent,
                'suggestions': suggestions,
                'map_data': map_data,
                'has_spatial_data': bool(coordinates or locations)
            }
            
        except Exception as e:
            logger.error(f"Error processing geospatial query: {str(e)}")
            return {
                'coordinates': [],
                'locations': [],
                'spatial_intent': 'unknown',
                'suggestions': [],
                'map_data': None,
                'has_spatial_data': False
            }
    
    def _classify_spatial_intent(self, query_text: str) -> str:
        """Classify the spatial intent of the query"""
        intent_patterns = {
            'data_coverage': [
                r'coverage.*area', r'data.*available.*for', r'satellite.*coverage',
                r'extent.*of.*data', r'boundary.*of.*data'
            ],
            'location_query': [
                r'where.*is', r'location.*of', r'find.*place', r'coordinates.*of'
            ],
            'spatial_analysis': [
                r'area.*calculation', r'distance.*between', r'spatial.*analysis',
                r'boundary.*analysis', r'overlap.*with'
            ],
            'data_download': [
                r'download.*data.*for', r'get.*data.*from', r'extract.*data.*for'
            ]
        }
        
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_text, re.IGNORECASE):
                    return intent
        
        return 'general_spatial'
    
    def _generate_spatial_suggestions(self, coordinates: List[Dict], 
                                    locations: List[Dict], intent: str) -> List[str]:
        """Generate helpful spatial suggestions based on the query"""
        suggestions = []
        
        if intent == 'data_coverage':
            suggestions.extend([
                "Check satellite data availability for your region",
                "View data coverage maps",
                "Browse available satellite products"
            ])
        
        if intent == 'location_query':
            suggestions.extend([
                "Use the map to explore the area",
                "Get precise coordinates",
                "Find nearby data points"
            ])
        
        if coordinates:
            suggestions.extend([
                "View data at these coordinates",
                "Check data quality for this location",
                "Download data for this area"
            ])
        
        if locations:
            suggestions.extend([
                f"Explore data for {locations[0]['name']}",
                "Get regional data statistics",
                "View historical data trends"
            ])
        
        if not coordinates and not locations:
            suggestions.extend([
                "Specify coordinates or location name",
                "Use the map to select an area",
                "Browse data by region"
            ])
        
        return suggestions[:5]  # Limit suggestions
    
    def _create_interactive_map(self, coordinates: List[Dict], 
                              locations: List[Dict]) -> Optional[Dict[str, Any]]:
        """Create an interactive map with the spatial data"""
        try:
            # Default center (India)
            center_lat, center_lon = 20.5937, 78.9629
            zoom_level = 5
            
            # Adjust center based on data
            if coordinates:
                center_lat = np.mean([coord['lat'] for coord in coordinates])
                center_lon = np.mean([coord['lon'] for coord in coordinates])
                zoom_level = 8
            elif locations:
                # Use bounds of first location with bounds
                for loc in locations:
                    if loc.get('bounds'):
                        bounds = loc['bounds']
                        center_lat = (bounds['min_lat'] + bounds['max_lat']) / 2
                        center_lon = (bounds['min_lon'] + bounds['max_lon']) / 2
                        zoom_level = 7
                        break
            
            # Create folium map
            m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level)
            
            # Add coordinate markers
            for coord in coordinates:
                folium.Marker(
                    [coord['lat'], coord['lon']],
                    popup=f"Coordinates: {coord['lat']:.4f}, {coord['lon']:.4f}",
                    tooltip="Click for details",
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)
            
            # Add location markers/areas
            for loc in locations:
                if loc.get('bounds'):
                    bounds = loc['bounds']
                    # Add rectangle for location bounds
                    folium.Rectangle(
                        bounds=[[bounds['min_lat'], bounds['min_lon']], 
                               [bounds['max_lat'], bounds['max_lon']]],
                        popup=f"Location: {loc['name']}",
                        color='blue',
                        fillOpacity=0.2
                    ).add_to(m)
                else:
                    # Add a marker at estimated location
                    folium.Marker(
                        [center_lat, center_lon],
                        popup=f"Location: {loc['name']}",
                        tooltip=loc['name'],
                        icon=folium.Icon(color='blue', icon='map-marker')
                    ).add_to(m)
            
            # Convert map to HTML string
            map_html = m._repr_html_()
            
            return {
                'html': map_html,
                'center': [center_lat, center_lon],
                'zoom': zoom_level,
                'has_data': bool(coordinates or locations)
            }
            
        except Exception as e:
            logger.error(f"Error creating interactive map: {str(e)}")
            return None
    
    def get_data_coverage_info(self, spatial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about data coverage for the spatial area"""
        try:
            coverage_info = {
                'satellites_available': [
                    'Oceansat-2', 'ResourceSat-2', 'INSAT-3D',
                    'Cartosat-2', 'Sentinel-1', 'Landsat-8'
                ],
                'data_products': [
                    'Ocean Color', 'Sea Surface Temperature',
                    'Land Surface Temperature', 'NDVI',
                    'Precipitation', 'Wind Speed'
                ],
                'temporal_coverage': '2008-present',
                'spatial_resolution': '1km - 56m',
                'update_frequency': 'Daily to Weekly'
            }
            
            # Add specific recommendations based on coordinates/locations
            if spatial_data.get('coordinates'):
                coord = spatial_data['coordinates'][0]
                if self._is_over_ocean(coord['lat'], coord['lon']):
                    coverage_info['recommended_products'] = [
                        'Ocean Color Data', 'Sea Surface Temperature',
                        'Wave Height', 'Ocean Winds'
                    ]
                else:
                    coverage_info['recommended_products'] = [
                        'Land Surface Temperature', 'NDVI',
                        'Land Cover', 'Digital Elevation Model'
                    ]
            
            return coverage_info
            
        except Exception as e:
            logger.error(f"Error getting coverage info: {str(e)}")
            return {}
    
    def _is_over_ocean(self, lat: float, lon: float) -> bool:
        """Simple check if coordinates are over ocean (simplified)"""
        # This is a very simplified check
        # In reality, you'd use a proper land/ocean mask
        indian_ocean_bounds = {
            'min_lat': -40, 'max_lat': 30,
            'min_lon': 20, 'max_lon': 120
        }
        
        return (indian_ocean_bounds['min_lat'] <= lat <= indian_ocean_bounds['max_lat'] and
                indian_ocean_bounds['min_lon'] <= lon <= indian_ocean_bounds['max_lon'])
    
    def generate_spatial_context(self, query_data: Dict[str, Any]) -> str:
        """Generate spatial context information for the query"""
        spatial_data = self.process_geospatial_query(query_data)
        
        if not spatial_data['has_spatial_data']:
            return "No specific spatial information detected in your query."
        
        context_parts = []
        
        if spatial_data['coordinates']:
            coord_count = len(spatial_data['coordinates'])
            context_parts.append(f"Found {coord_count} coordinate location(s) in your query.")
        
        if spatial_data['locations']:
            loc_names = [loc['name'] for loc in spatial_data['locations']]
            context_parts.append(f"Identified locations: {', '.join(loc_names[:3])}")
        
        intent = spatial_data['spatial_intent']
        if intent != 'unknown':
            context_parts.append(f"This appears to be a {intent.replace('_', ' ')} query.")
        
        return " ".join(context_parts)