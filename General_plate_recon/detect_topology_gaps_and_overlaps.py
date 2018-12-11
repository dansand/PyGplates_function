#
# This script resolves topological plate polygons (and deforming networks) through time and detects
# any gaps and overlaps in their global coverage. Anomalous sub-segments, locating the gaps/overlaps,
# are written to a file that can be loaded into GPlates to visualise alongside the dynamic plate polygons.
# 
# Gaps and overlaps are caused when:
# 
#   1) there is an area of the globe not covered by a topological boundary or network, or
#   2) two (or more) topological boundary polygons overlap in some area of the globe.
# 
# This can also happen if two topological line sections are identical when ideally there should only
# be one of them (and it should be shared by two neighbouring topological boundaries).
#
# This script also detects any subduction zones with missing subduction polarity (or specified as unknown).
#

import pygplates


# Load one or more rotation files into a rotation model.
rotation_model = pygplates.RotationModel([
    '/Users/Andrew/Documents/EarthByte_Models/Global_1000-0_Model_2017/1000-410_rotations.rot',
])

# Load the topological plate polygon features (can also include deforming networks).
topology_features = [
    pygplates.FeatureCollection('/Users/Andrew/Documents/EarthByte_Models/Global_1000-0_Model_2017/1000-410-Convergence.gpml',
                                            '/Users/Andrew/Documents/EarthByte_Models/Global_1000-0_Model_2017/1000-410-Divergence.gpml',
                                            '/Users/Andrew/Documents/EarthByte_Models/Global_1000-0_Model_2017/1000-410-Topologies.gpml',
                                            '/Users/Andrew/Documents/EarthByte_Models/Global_1000-0_Model_2017/1000-410-Transforms.gpml')
]

# Should we output anomalous features as *reconstructed* (which means *resolved* in the case of sub-segments)
# such that they don't have to be reconstructed when visualising in GPlates?
# Setting this to False can be useful when visualising in GPlates with the topologies loaded in the background
# (in which case the rotation model will also be loaded since it's needed to resolve the background topologies in GPlates).
# Setting this to True can be useful when visualising them in GPlates *without* a rotation model loaded.
output_reconstructed_anomalous_features = False

# Whether to output all time steps to a single file (one for sub-segments and one for subduction zones) and
# whether to output each time step to a single file (one for sub-segments and one for subduction zones, for each time step).
output_all_time_steps_to_a_single_file = True
output_each_time_step_to_a_single_file = False

# Does an 'Unknown' subduction polarity count as anomalous (ie, needs to be rectified).
# Note: A missing subduction polarity is always counted as anomalous.
subduction_polarity_unknown_is_anomalous = True


# Our geological times will be from 0Ma to 'num_time_steps' Ma (inclusive) in 1 My intervals.
num_time_steps = 1000

# All anomalous sub-segment features (where gaps and overlaps are located).
all_anomalous_sub_segment_features = []

# All subduction zone features (used in topology boundaries) that don't have a subduction polarity property.
all_anomalous_subduction_features = []

# 'time' = 0, 1, 2, ...
for time in range(410,num_time_steps + 1):

    print 'Time: %f' % time
    
    # Resolve our topological plate polygons (and deforming networks) to the current 'time'.
    # We generate both the resolved topology boundaries and the boundary sections between them.
    resolved_topologies = []
    shared_boundary_sections = []
    pygplates.resolve_topologies(topology_features, rotation_model, resolved_topologies, time, shared_boundary_sections)

    # We'll create a feature for any anomalous sub-segment we find.
    anomalous_sub_segment_features = []

    # We'll reference any existing subduction zone features that don't have a subduction polarity property.
    # Note: Only those subduction zones that are actually used to resolve a topology are considered.
    anomalous_subduction_features = []

    # Iterate over the shared boundary sections.
    for shared_boundary_section in shared_boundary_sections:
        
        # Keep track of any subduction zones with anomalous subduction polarities.
        if shared_boundary_section.get_feature().get_feature_type() == pygplates.FeatureType.gpml_subduction_zone:
            subduction_polarity = shared_boundary_section.get_feature().get_enumeration(pygplates.PropertyName.gpml_subduction_polarity)
            # Subduction polarity is anomalous if it's either missing (or specified as unknown, if that counts as anomalous).
            if ((not subduction_polarity) or
               (subduction_polarity_unknown_is_anomalous and (subduction_polarity == 'Unknown'))):
                    anomalous_subduction_features.append(shared_boundary_section.get_feature())
        
        # Iterate over the sub-segments that actually contribute to a topology boundary.
        for shared_sub_segment in shared_boundary_section.get_shared_sub_segments():

            # If the resolved topologies have global coverage with no gaps/overlaps then
            # each sub-segment should be shared by exactly two resolved boundaries.
            if len(shared_sub_segment.get_sharing_resolved_topologies()) != 2:

                # The sub-segment is anomalous so it's possible we've already emitted the sub-segment.
                # If so then remove it - we're not including anomalous geometries that are exact duplicates.
                duplicate_index = None
                for index, anomalous_feature in enumerate(anomalous_sub_segment_features):
                    # Test for duplicate geometry or reversed duplicate.
                    anomalous_geometry = anomalous_feature.get_geometry(lambda property: True)
                    if (shared_sub_segment.get_geometry() == anomalous_geometry or
                        shared_sub_segment.get_geometry() == pygplates.PolylineOnSphere(reversed(anomalous_geometry))):
                        duplicate_index = index
                        break
                
                # If we've not already emitted the sub-segment then emit it now.
                if duplicate_index is None:
                    # We keep track of any anomalous sub-segment features.
                    anomalous_sub_segment_features.append(shared_sub_segment.get_resolved_feature())
                else:
                    anomalous_sub_segment_features.pop(duplicate_index)

    # If there are any anomalous features for the current 'time' then write them to a file
    # so we can load them into GPlates and see where the errors are located.
    if anomalous_sub_segment_features:
        
        # The anomalous sub-segments are resolved (ie, reconstructed).
        # If they should be regular un-reconstructed features (ie, that store present-day geometries)
        # then we'll need to reverse reconstruct them.
        if not output_reconstructed_anomalous_features:
            # Clone the features to be sure we don't interfere with resolving topologies in subsequent time steps.
            # This is not actually necessary since the resolve sub-segments are already cloned but we'll clone
            # anyway since that's not guaranteed by the pyGPlates API.
            anomalous_sub_segment_features = [anomalous_feature.clone() for anomalous_feature in anomalous_sub_segment_features]
            pygplates.reverse_reconstruct(anomalous_sub_segment_features, rotation_model, time)
        
        if output_each_time_step_to_a_single_file:
            # Put the anomalous sub-segment features in a feature collection so we can write them to a file.
            anomalous_sub_segment_feature_collection = pygplates.FeatureCollection(anomalous_sub_segment_features)

            # Create a filename (for anomalous sub-segment features) with the current 'time' in it.
            anomalous_sub_segment_features_filename = 'anomalous_sub_segments_at_{0}Ma.gpml'.format(time)

            # Write the anomalous sub-segments to a new file.
            anomalous_sub_segment_feature_collection.write(anomalous_sub_segment_features_filename)
        
        # Modify the time periods such that the features are only visible for the current time.
        # Note that we do this *after* writing to the GPML file for the current time.
        for feature in anomalous_sub_segment_features:
            feature.set_valid_time(time + 0.5, time - 0.5)
        
        # Add to list over all times.
        all_anomalous_sub_segment_features.extend(anomalous_sub_segment_features)

    if anomalous_subduction_features:
        
        if output_reconstructed_anomalous_features:
            # We want to output *reconstructed* subduction zones so clone the existing subduction zone features
            # (we don't want to interfere with resolving topologies in subsequent time steps) and
            # replace their present day geometries with reconstructed versions.
            subduction_reconstructed_features = []
            pygplates.reconstruct(anomalous_subduction_features, rotation_model, subduction_reconstructed_features, time, group_with_feature=True)
            
            anomalous_subduction_features = []
            for feature, reconstructed_geometries in subduction_reconstructed_features:
                reconstructed_feature = feature.clone()
                # We're assuming all geometries in the current feature have the same (default) property name.
                # This is not always the case but should be fine since we're just want to visualise their locations in GPlates.
                # And in most cases there's only one geometry anyway.
                reconstructed_feature.set_geometry([reconstructed_geometry.get_reconstructed_geometry()
                                                    for reconstructed_geometry in reconstructed_geometries])
                anomalous_subduction_features.append(reconstructed_feature)
        
        if output_each_time_step_to_a_single_file:
            # Put the anomalous subduction features in a feature collection so we can write them to a file.
            anomalous_subduction_feature_collection = pygplates.FeatureCollection(anomalous_subduction_features)

            # Create a filename (for anomalous subduction features) with the current 'time' in it.
            anomalous_subduction_features_filename = 'anomalous_subduction_zones_at_{0}Ma.gpml'.format(time)

            # Write the anomalous subduction zones to a new file.
            anomalous_subduction_feature_collection.write(anomalous_subduction_features_filename)
        
        # Modify the time periods such that the features are only visible for the current time.
        # Note that we do this *after* writing to the GPML file for the current time.
        for feature in anomalous_subduction_features:
            feature.set_valid_time(time + 0.5, time - 0.5)
        
        # Add to list over all times.
        all_anomalous_subduction_features.extend(anomalous_subduction_features)

# If there are any anomalous features for any time then write them all to a file
# so we can load them into GPlates and see where the errors are located.
if all_anomalous_sub_segment_features and output_all_time_steps_to_a_single_file:
    
    # Put all anomalous sub-segment features in a feature collection so we can write them to a file.
    all_anomalous_sub_segment_feature_collection = pygplates.FeatureCollection(all_anomalous_sub_segment_features)

    # Create a filename (for anomalous sub-segment features) with the current 'time' in it.
    all_anomalous_sub_segment_features_filename = 'all_anomalous_sub_segments.gpml'

    # Write the anomalous sub-segments to a new file.
    all_anomalous_sub_segment_feature_collection.write(all_anomalous_sub_segment_features_filename)

if all_anomalous_subduction_features and output_all_time_steps_to_a_single_file:
    
    # Put all anomalous subduction features in a feature collection so we can write them to a file.
    all_anomalous_subduction_feature_collection = pygplates.FeatureCollection(all_anomalous_subduction_features)

    # Create a filename (for anomalous subduction features) with the current 'time' in it.
    all_anomalous_subduction_features_filename = 'all_anomalous_subduction_zones.gpml'

    # Write the anomalous subduction zones to a new file.
    all_anomalous_subduction_feature_collection.write(all_anomalous_subduction_features_filename)
