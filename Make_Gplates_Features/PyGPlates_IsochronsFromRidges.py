
"""
    Copyright (C) 2014 The University of Sydney, Australia
    
    This program is free software; you can redistribute it and/or modify it under
    the terms of the GNU General Public License, version 2, as published by
    the Free Software Foundation.
    
    This program is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
    for more details.
    
    You should have received a copy of the GNU General Public License along
    with this program; if not, write to Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

from optparse import OptionParser
from optparse import OptionValueError
import pygplates


def create_left_and_right_isochrons(
        isochron_feature_collection,
        rotation_model,
        mid_ocean_ridge_feature,
        left_plate_id,
        right_plate_id,
        time_of_appearance):
    
    # Reconstruct the mid-ocean ridge to its time of appearance.
    # The reconstructed geometry(s) will be in the same position as the left/right isochrons at that time.
    mid_ocean_ridge_reconstructed_feature_geometries = []
    pygplates.reconstruct(mid_ocean_ridge_feature, rotation_model, mid_ocean_ridge_reconstructed_feature_geometries, time_of_appearance)
    isochron_geometries_at_time_of_appearance = [reconstructed_feature_geometry.get_reconstructed_geometry()
            for reconstructed_feature_geometry in mid_ocean_ridge_reconstructed_feature_geometries]
    
    # Create the left and right isochrons (and reverse reconstruct the mid-ocean ridge geometries to present).
    left_isochron_feature = pygplates.Feature.create_reconstructable_feature(
            pygplates.FeatureType.create_gpml('Isochron'),
            isochron_geometries_at_time_of_appearance,
            name = mid_ocean_ridge_feature.get_name(None),
            description = mid_ocean_ridge_feature.get_description(None),
            valid_time = (time_of_appearance, 0),
            reconstruction_plate_id = left_plate_id,
            other_properties = [(pygplates.PropertyName.create_gpml('conjugatePlateId'), pygplates.GpmlPlateId(right_plate_id))],
            reverse_reconstruct = (rotation_model, time_of_appearance))
    right_isochron_feature = pygplates.Feature.create_reconstructable_feature(
            pygplates.FeatureType.create_gpml('Isochron'),
            isochron_geometries_at_time_of_appearance,
            name = mid_ocean_ridge_feature.get_name(None),
            description = mid_ocean_ridge_feature.get_description(None),
            valid_time = (time_of_appearance, 0),
            reconstruction_plate_id = right_plate_id,
            other_properties = [(pygplates.PropertyName.create_gpml('conjugatePlateId'), pygplates.GpmlPlateId(left_plate_id))],
            reverse_reconstruct = (rotation_model, time_of_appearance))
    
    # Add isochrons to feature collection.
    isochron_feature_collection.add(left_isochron_feature)
    isochron_feature_collection.add(right_isochron_feature)

        
def generate_isochrons(
        isochron_feature_collection,
        rotation_feature_collection,
        mid_ocean_ridge_feature_collection,
        mid_ocean_ridge_left_plate_id,
        mid_ocean_ridge_right_plate_id,
        mid_ocean_ridge_begin_time,
        mid_ocean_ridge_end_time,
        isochron_creation_times):
    
    # All rotation queries go through this.
    rotation_model = pygplates.RotationModel([rotation_feature_collection])
    
    for mid_ocean_ridge_feature in mid_ocean_ridge_feature_collection:
        # Ignore anything that's not a mid-ocean ridge.
        if mid_ocean_ridge_feature.get_feature_type() != pygplates.FeatureType.create_gpml('MidOceanRidge'):
            continue
        
        # Get the MOR left and right plate ids, and time of appearance.
        left_plate_id = mid_ocean_ridge_feature.get_left_plate(None)
        right_plate_id = mid_ocean_ridge_feature.get_right_plate(None)
        valid_time = mid_ocean_ridge_feature.get_valid_time(None)
        
        # Ignore mid-ocean ridges that don't have a left and right plate id and time of appearance.
        if left_plate_id is None or right_plate_id is None or valid_time is None:
            continue
        
        time_of_appearance, time_of_disappearance = valid_time
        
        # If filtering mid-ocean ridges by left and/or right plate id then ignore those that don't match.
        if mid_ocean_ridge_left_plate_id and left_plate_id != mid_ocean_ridge_left_plate_id:
            continue
        if mid_ocean_ridge_right_plate_id and right_plate_id != mid_ocean_ridge_right_plate_id:
            continue
        
        # If filtering mid-ocean ridges by time interval then ignore those with birth times outside interval.
        if mid_ocean_ridge_begin_time and time_of_appearance > mid_ocean_ridge_begin_time:
            continue
        if mid_ocean_ridge_end_time and time_of_appearance < mid_ocean_ridge_end_time:
            continue
        
        if isochron_creation_times:
            # We have a list of creation times for the left/right isochrons.
            for isochron_creation_time in isochron_creation_times:
                # If creation time is later than ridge birth time then we can create an isochron.
                if isochron_creation_time < time_of_appearance:
                    create_left_and_right_isochrons(
                            isochron_feature_collection,
                            rotation_model,
                            mid_ocean_ridge_feature,
                            left_plate_id,
                            right_plate_id,
                            isochron_creation_time)
        else:
            # Else create left/right isochrons at the ridge birth time.
            create_left_and_right_isochrons(
                    isochron_feature_collection,
                    rotation_model,
                    mid_ocean_ridge_feature,
                    left_plate_id,
                    right_plate_id,
                    time_of_appearance)

    input_rotation_filename = args[0]
    input_mid_ocean_ridge_filename = args[1]
    output_isochron_filename = args[2]

    file_registry = pygplates.FeatureCollectionFileFormatRegistry()
    
    # Read/parse the rotation feature collection.
    rotation_feature_collection = file_registry.read(input_rotation_filename)
    
    # Read/parse the mid-ocean ridge feature collection.
    mid_ocean_ridge_feature_collection = file_registry.read(input_mid_ocean_ridge_filename)
    
    # Create empty isochron feature collection.
    isochron_feature_collection = pygplates.FeatureCollection()
    
    # Generate isochrons and fill isochron feature collection.
    generate_isochrons(
            isochron_feature_collection,
            rotation_feature_collection,
            mid_ocean_ridge_feature_collection,
            options.left_plate_id,
            options.right_plate_id,
            options.begin_time,
            options.end_time,
            options.creation_times)
    
    # Write the isochron feature collection to disk.
    file_registry.write(isochron_feature_collection, output_isochron_filename)
