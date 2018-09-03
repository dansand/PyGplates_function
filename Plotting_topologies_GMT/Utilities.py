import sys
sys.path.insert(1, '/Users/Andrew/Documents/PhD/Scripts/Python/pygplates_rev12')
import pygplates
import numpy as np

centre_longitude = 180
date_line_wrapper = pygplates.DateLineWrapper(centre_longitude)

def Get_FZ_Directions(X1,Y1,X2,Y2):

    #to determine orientation of MOR from north from flowline segments
    #x1/y1 lat/lon start point of MOR
    #x2/y2 lat/lon end point of MOR
    
    long1 = np.radians(X1)
    long2 = np.radians(X2)
    lat1 = np.radians(Y1)
    lat2 = np.radians(Y2)

    bearing = np.arctan2(np.sin(long2-long1)*np.cos(lat2), np.cos(lat1)*np.sin(lat2)-np.sin(lat1)*np.cos(lat2)*np.cos(long2-long1))
    bearing = np.degrees(bearing)
    bearing = (bearing + 360) % 360

    return bearing

def poles_of_rotation(to_time, from_time, delta_time, rotation_model, moving_plate, fixed_plate):

    #loop through a rotation in specific time intervals to extract poles of rotation between two plates

    #create variables
    Lats = []
    Longs = []
    Angles = []
    time_change = []
    
    for time in np.arange(to_time,from_time,delta_time):

        to_time = time
        from_time = time+delta_time
        stage_rotation = rotation_model.get_rotation(to_time,moving_plate,from_time,fixed_plate)

        pole_lat,pole_lon,pole_angle = stage_rotation.get_lat_lon_euler_pole_and_angle_degrees()

        #to make sure that all poles are expressed in the same hemisphere
        if pole_angle < 0:
            pole_lat = -1*pole_lat
            pole_lon = pole_lon-180
            pole_angle = -1*pole_angle


        time_change.append(from_time)
        #print 'Time interval = ',time,'-',time+delta_time,', Stage Pole Lat,Lon,Angle = %f,%f,%f ' % (pole_lat,pole_lon,pole_angle) #check values if necessary
        Lats.append(pole_lat)
        Longs.append(pole_lon)
        Angles.append(np.radians(pole_angle))

    # These next lines are necessary becuase the answers come out in the northern hemisphere, 
    # need to check convention
    Longs = np.add(Longs,180.)
    Lats = np.multiply(Lats,-1)
    
    return Longs, Lats, Angles, time_change

def plotting_geometries(rotation_model, topology_features, time, delta_time):
    
    #extract geometries from a reconstructed file for plotting
    
    all_reconstructed_points = []
    all_velocities = []
    xy_reconstructed_points = []
    
    for feature in topology_features:

        # We need the feature's plate ID to get the equivalent stage rotation of that tectonic plate.
        domain_plate_id = feature.get_reconstruction_plate_id()

        # Get the rotation of plate 'domain_plate_id' from present day (0Ma) to 'reconstruction_time'.
        equivalent_total_rotation = rotation_model.get_rotation(time, domain_plate_id)

        # Get the rotation of plate 'domain_plate_id' from 'reconstruction_time + delta_time' to 'reconstruction_time'.
        equivalent_stage_rotation = rotation_model.get_rotation(time, domain_plate_id, time + delta_time)

        for geometry in feature.get_geometries():

            # Reconstruct the geometry to 'reconstruction_time'.
            reconstructed_geometry = equivalent_total_rotation * geometry
            reconstructed_points = reconstructed_geometry.get_points()
            xy_reconstructed_points = reconstructed_points.to_lat_lon_array()

            all_reconstructed_points.append(xy_reconstructed_points)

    poly_longs = []
    poly_lats = []
    for i in all_reconstructed_points:
        j = i[:,0]
        k = i[:,1]
        poly_longs.append(k)
        poly_lats.append(j)
        
    return poly_lats, poly_longs, all_reconstructed_points

def wrapping_polysomethings(poly_lats, poly_longs):
    #
    #needs pygplates
    #to wrap polygons around the dateline for plotting 
    #
    
    latitudes = np.asarray(poly_lats)
    longitudes = np.asarray(poly_longs)
    polyline = pygplates.PolylineOnSphere(zip(latitudes, longitudes))
    wrapped_polylines = date_line_wrapper.wrap(polyline)
    for wrapped_polyline in wrapped_polylines:
        wrapped_points = wrapped_polyline.get_points()
        wrapped_points_lat = []
        wrapped_points_lon = []
        for wrapped_point in wrapped_points:
            wrapped_point_lat, wrapped_point_lon = wrapped_point.get_latitude(), wrapped_point.get_longitude()
            wrapped_points_lat.append(wrapped_point_lat)
            wrapped_points_lon.append(wrapped_point_lon)

        wrapped_points_lat = np.array(wrapped_points_lat)
        wrapped_points_lon = np.array(wrapped_points_lon)

        return wrapped_points_lat, wrapped_points_lon