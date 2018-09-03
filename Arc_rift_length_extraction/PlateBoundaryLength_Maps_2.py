# -*- coding: utf-8 -*-
# this script is based on Plot-SubductionStats-Volumes_sb4.py see '/Users/brune/_prog/pygplates/11_SubductionStats/'

# -*- coding: utf-8 -*-
import sys
sys.path.insert(1, '/Users/brune/Software/pygplates/pygplates_latest')
sys.path.append('/Users/brune/_prog/pygplates/00_Utils')
#print 'Write out sys.path: ' + str(sys.path)

import pygplates
import numpy as np
import os
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from topology_plotting_sb1 import *
from matplotlib.patches import Polygon
from scipy.special import erfinv
import pandas as pd

##############################################################################################################
# Flags, Paramaters, Input Files
##############################################################################################################
save_yn=0
PlotReconstructedRifts_yn = 0
PlotSengorRifts_yn = 1
PlotSubduction_yn = 0
PlotContinentalArcs_yn = 0
# MORs are always plotted, modify plot_velocities_and_topologies_sb in 00_Utils if you don't like that.

# Time range
tStep = 1
tStart = 200
tEnd = 0


trunc = '/Users/brune/_prog/pygplates/04_PlateBoundaryLength/'
outputFolder = trunc + 'RiftsSubMOR_NoSengor_1My_new/'
tempFolder = trunc + 'tmp/'
rotation_filename = trunc + 'Data/Global_EarthByte_230-0Ma_GK07_AREPS.rot' # rotation file

# Input topologies to be used with the subduction_convergence script
input_topology_filename = [trunc + 'Data/Global_EarthByte_230-0Ma_GK07_AREPS_PlateBoundaries_SB2.gpmlz',\
                           trunc + 'Data/Global_EarthByte_230-0Ma_GK07_AREPS_Topology_BuildingBlocks.gpmlz']

# Coastlines
coastlines_file = trunc + 'Data/Global_EarthByte_230-0Ma_GK07_AREPS_Coastlines.gpmlz'

# Static polygons to determine whether subduction segment is adjacent to continent or not
static_polygon_filename = trunc + 'Data/Global_EarthByte_GPlates_PresentDay_StaticPlatePolygons_2015_v1_SB.gpmlz'

# Rift database
PathToSengorsRiftCsv = trunc + '../09_Rifts_SengorNatalin/_input/rifts_sb.csv'

# Geological Time Scale Hierarchy
TimescaleHierarchy = trunc + '../09_Rifts_SengorNatalin/_input/TimescaleHierarchy.csv'

##############################################################################################################
# Functions
##############################################################################################################
def AgeRangeFromString(age_string):
    #age_string = 'Late Miocene'
    subset = ts.where(ts.Age.str.match(age_string,case=False) | 
                    ts.SubEpoch.str.match(age_string,case=False) | 
                    ts.Epoch.str.match(age_string,case=False) | 
                    ts.Period.str.match(age_string,case=False)).dropna()

    age_range = (np.min(subset.End_Ma),np.max(subset.Start_Ma))
    
    return age_range
    
##############################################################################################################
# Load Rotations and Static polygons
##############################################################################################################
rotation_model = pygplates.RotationModel(rotation_filename)

## specify time range and resolution for plots
#threshold_sampling_distance_radians = np.radians(0.5)

static_polygon_features = pygplates.FeatureCollection(static_polygon_filename)
continental_polygon_features = []
for feature in static_polygon_features:
    if feature.get_feature_type() == pygplates.FeatureType.gpml_closed_continental_boundary:
        continental_polygon_features.append(feature)
        
##############################################################################################################
### load subduction data file
### subduction volume not needed for now, but a nice template to get subduction rates
##############################################################################################################
# Define the time snapshots at which to get the subduction zone properties
#min_time = 0.
#max_time = 200.
#time_step = 5.
#
## Set the delta time for velocity calculations
#velocity_delta_time = 5.

# Typically the achor plate id should be 0
anchor_plate_id = 0

# Example of loading previously calculated results from a hdf5 file as created using the line above
df = pd.read_hdf(trunc + 'Data/SubductionTable_0_200Ma.h5')

#mr = np.asarray(df['migr_rate'])
#mo = np.asarray(df['migr_obliq'])
#df['ortho_migr_rate'] = pd.Series(mr*np.sin(np.radians(np.abs(mo))), index=df.index)

### Subduction Volumes
#T1 = 1300.
#To = 0.
#Tm = 1600.
#kappa = 8e-8
#Myr2sec=1e6*365*24*60*60
#lithosphere_thickness = erfinv((T1-To)/(Tm-To))*2*np.sqrt(kappa)*np.sqrt(Myr2sec*np.asarray(df['SeafloorAge']))
#
#print len(df)
#print np.asarray(df['SeafloorAge'])
#print lithosphere_thickness
##print pd.Series(lithosphere_thickness)
#
#df['subduction_volume'] = pd.Series(
#    np.asarray(df['arc_length']) * 111. * np.asarray(df['conv_rate']) * lithosphere_thickness,
#    index=df.index)
#df['lithosphere_thickness'] = pd.Series(lithosphere_thickness, index=df.index)
#
df_AllTimes = df

# Display the contents of the table containing all subduction
df

##############################################################################################################
# Load and prepare Sengörs rifts for plotting largerely copy-pasted from original python notebook: 
# 09_Rifts_SengorNatalin/Rifts-of-the-world-sb3.ipynb
##############################################################################################################
# load rifts
rifts_df = pd.read_csv(PathToSengorsRiftCsv)

# load geological time scale hierarchy 
ts = pd.read_csv(TimescaleHierarchy)

# assign age of rifts
amax = []
amin = []

for index,rift in rifts_df.iterrows():
    ar1 = (np.nan,np.nan) # age range start
    ar2 = (np.nan,np.nan) # age range end
    
    if pd.notnull(rift.Old_Age):
        ar1 = AgeRangeFromString(rift.Old_Age)
        if np.isnan(ar1[0]):
            # This is supposed to catch entries whose age name does not match anything
            # in the list
            print 'no match for %s' % rift.Old_Age
            print rift.Region + rift.ID + ': Old_Age ' + rift.Old_Age
        #print rift.Region + rift.ID + ': Old_Age ' + rift.Old_Age + '. ar1[0] ' + str(ar1[0])+ '. ar1[1] ' + str(ar1[1])  
    
    if pd.notnull(rift.Young_Age):
        ar2 = AgeRangeFromString(rift.Young_Age)
        #print rift.Region + rift.ID + ': Young_Age ' + rift.Young_Age + '. ar2[0] ' + str(ar2[0])+ '. ar2[1] ' + str(ar2[1])  
        
    #print (ar1[1],ar2[1])
    tmp1 = np.nanmax([ar1,ar2])
    tmp2 = np.nanmin([ar1,ar2])
    amax.append(tmp1)
    amin.append(tmp2)
    
#print rift.Old_Age,rift.Young_Age,ar1,ar2,tmp1,tmp2
rifts_df['Old_Age_Ma'] = pd.Series(amax)
rifts_df['Young_Age_Ma'] = pd.Series(amin)

### This List excludes EARS, Red Sea, CARS, WARS, Antarctica from the analysis. (already in pygplates-rift database)
# 05_NoMargins_ExcludingOverlappingRifts
WEUR_out=['62','63','81','83','84','85','118']
EEUR_out=['29','36','37','43','58','59','63','64','72','73','74','75','76','77','78','110']
AFR_out=['8','14','15Ia','15Ie','15Ie1','15If','15IIa','15IIb','15IIc','15IId','15IId1','15IIe','16','18','19','21','22','23','24','26','27','28','25','31','32','33','34','35','36','37','38','39','40','41','48','49','59','60','61','62','65','67','70','71','74','88']
MAD_out=['']
AUS_out=['5a','5b','5c','5d','5e','5f','7a','7b']
NZ_out=['']
NAM_out=['18','22','23','24','31','32','33','34','35','36','37','38','39','40','41','42','43','44','45','46','47','48','49','50','51','52']
CAM_out=['']
SAM_out=['35','38','39','40','41','42','43','44','45','46','49','50','51','52','53']
ANT_out=['5a','5b','5c','11']
rifts_df = rifts_df.where( (rifts_df.Region.str.contains('WEUR')) & ~rifts_df.ID.isin(WEUR_out) |
                        (rifts_df.Region.str.contains('EEUR')) & ~rifts_df.ID.isin(EEUR_out) |
                        (rifts_df.Region.str.contains('AFR'))  & ~rifts_df.ID.isin(AFR_out) |
                        (rifts_df.Region.str.contains('MAD'))  & ~rifts_df.ID.isin(MAD_out) |
                        (rifts_df.Region.str.contains('AUS'))  & ~rifts_df.ID.isin(AUS_out) |
                        (rifts_df.Region.str.contains('NZ'))   & ~rifts_df.ID.isin(NZ_out) |
                        (rifts_df.Region.str.contains('NAM'))  & ~rifts_df.ID.isin(NAM_out) |
                        (rifts_df.Region.str.contains('CAM'))  & ~rifts_df.ID.isin(CAM_out) |
                        (rifts_df.Region.str.contains('SAM'))  & ~rifts_df.ID.isin(SAM_out) |
                        (rifts_df.Region.str.contains('ANT'))  & ~rifts_df.ID.isin(ANT_out)   
                    ) 
                    
### get rid of rifts that are older than start time
rifts_df = rifts_df.where(rifts_df.Young_Age_Ma<tStart)

### resolve some dateline problems by modifying longitude by hand
i = rifts_df[ rifts_df.Name == 'North Chukchi' ].index.tolist()
rifts_df.set_value(i,'Long_Min',165)

##############################################################################################################
# Begin of time loop
##############################################################################################################
time_bins = np.arange(tStart,tEnd-tStep,-tStep)

for time in time_bins:
    
    # get subduction data for current time
    subset = df_AllTimes[(df_AllTimes['time']==time)]
    # reconstruct coastlines and polygons to current time
    pygplates.reconstruct(coastlines_file, rotation_model, tempFolder + 'tmp.shp', time)
    pygplates.reconstruct(continental_polygon_features, rotation_model, tempFolder + 'tmp2.shp', time)
    
    # prepare figure
    fig = plt.figure(figsize=(11,6),dpi=150)
    ax_map = fig.add_axes([0.01,0.01,0.98,0.98])
    lon0=0
    m = Basemap(projection='moll', lon_0=lon0, resolution='c', ax=ax_map)
    #m = Basemap(resolution='c',projection='ortho',lat_0=30.,lon_0=lon0)
    cp = m.drawmapboundary()
    m.drawparallels(np.arange(-90,90,30),linewidth=1,color=[220.0/255,220.0/255,220.0/255],dashes=[100,.0001],zorder=0) # grey
    m.drawmeridians(np.arange(-180,180,30),linewidth=1,color=[220.0/255,220.0/255,220.0/255],dashes=[100,.0001],zorder=0) # grey
    plt.title('                                                                                                           %s Ma' % time, size=16)

    # Plot reconstructed coastlines
    shp_info = m.readshapefile(tempFolder + 'tmp','shp',drawbounds=True,color='none')
    for nshape,seg in enumerate(m.shp):
        poly = Polygon(seg,facecolor='grey',edgecolor='none',alpha=0.5,zorder=0.5)
        plt.gca().add_patch(poly)
    
    # Plot reconstructed continental polygons
    shp_info = m.readshapefile(tempFolder + 'tmp2','shp',drawbounds=True,color='none')
    for nshape,seg in enumerate(m.shp):
        poly = Polygon(seg,facecolor='grey',edgecolor='none',alpha=0.3,zorder=0.25)
        plt.gca().add_patch(poly)
            
    #sb note this requires the utils directory 
    #plot_velocities_and_topologies(m,input_topology_filename,rotation_model,time,
    #                               delta_time=5,res=10,scale=4000,lon0=lon0,clip_path=cp)
    #sb I added a flag to this function for switching velocities on and off
    plot_velocities_and_topologies_sb(m,input_topology_filename,rotation_model,time,
                                delta_time=5,res=10,scale=1000,lon0=lon0,clip_path=cp,plotvel_yn=False,plotrest_yn=True)
    
    # plot distance to continent in color                            
    #x, y = m(np.asarray(subset.lon), np.asarray(subset.lat))
    #l1 = m.scatter(x,y,c=subset['DistanceToContinent']*pygplates.Earth.mean_radius_in_kms,s=40,edgecolor='',zorder=5,
    #               cmap=plt.cm.afmhot_r,vmin=-200,vmax=400)
    
    if PlotSubduction_yn:
        # plot subduction zones in black
        x, y = m(np.asarray(subset.lon), np.asarray(subset.lat))
        l1 = m.scatter(x,y,c=[0.3,0.3,0.3],s=40,edgecolor='',zorder=5)
            
    if PlotContinentalArcs_yn:            
        # distinguish between intra-oceanic subduction and ocean-continent subduction
        threshold = 170 # Stern (2002) has a mean trench-arc distance of 166+-60
        #df_IO = df[df['DistanceToContinent']*pygplates.Earth.mean_radius_in_kms>threshold]
        subset_OC = subset[subset['DistanceToContinent']*pygplates.Earth.mean_radius_in_kms<threshold]
    
        # plot ocean-continent subduction in orange #############################################################
        x, y = m(np.asarray(subset_OC.lon), np.asarray(subset_OC.lat))
        l1 = m.scatter(x,y,c=[236.0/255,171.0/255,19.0/255],s=50,edgecolor='',zorder=5) # orange
    
    # add rifts from pygplates analysis ######################################################################
    time_str=str(time)
    
    if PlotReconstructedRifts_yn:
        # add rifts from pygplates analysis ######################################################################
        riftdatabase='/Users/brune/_prog/pygplates/results/04_SerenasSimplePolygons/25a_v29_SriLanka_outer/14_PMarg_Rifts/_A_InterfaceData/times/'
        df = pd.read_csv(riftdatabase + time_str.zfill(3) + '.csv')
        arr = np.array(df)
        riftlon = arr[:,0]
        riftlat = arr[:,1]
        riftvel = arr[:,2]
        riftalpha = arr[:,3]
        riftvel = arr[:,0]
        riftx, rifty = m(np.asarray(riftlon), np.asarray(riftlat))
        l2 = m.scatter(riftx,rifty,c=[220.0/255,60.0/255,60.0/255],s=40,edgecolor='',zorder=5) # red
        
    if PlotSengorRifts_yn:
        #sb add Sengör rifts #####################################################################################
        ### pick rifts that are active in the current time bin (symmetric, centered bins)
        point_features = []
        partitioned_points = []
        rift_Id = []
        rift_Length = []
        for index,row in rifts_df.iterrows():
            if ((row.Old_Age_Ma>=time-tStep/2) & (row.Young_Age_Ma<time+tStep/2)):
                point_latitude = np.nanmean((row.Lat_Min,row.Lat_Max))
                point_longitude = np.nanmean((row.Long_Min,row.Long_Max))
                if np.isnan(point_latitude) | np.isnan(point_longitude):
                    print 'Error: Point location is NaN:'
                    print str(row.Region) + ': ' + str(row.ID)
                # bundle points to point feature
                point_feature = pygplates.Feature()
                point_feature.set_geometry(pygplates.PointOnSphere(point_latitude, point_longitude))
                # assign plate ID with GPlates function 'PlatePartitioner'
                partitioned_point = pygplates.partition_into_plates(static_polygon_features, rotation_model, point_feature)
                partitioned_points.append(partitioned_point)
                # append rift ID, Length
                rift_Id.append(row.ID)
                rift_Length.append(row.Length)
                
        # reconstruct points to shape file
        pygplates.reconstruct(partitioned_points, rotation_model, tempFolder + 'tmp3.shp', time)
        # load shape file
        m.readshapefile(tempFolder + 'tmp3','loaded_points')
        
        # plot Sengors rifts - for annotation uncomment the line
        for index,p in enumerate(m.loaded_points):
            m.plot(p[0], p[1], marker='o', color=[220.0/255,60.0/255,60.0/255],alpha=0.7, markersize=rift_Length[index]/100, markeredgewidth=1, zorder=6)
            #ax_map.annotate(str(rift_Id[index]), (p[0], p[1]),horizontalalignment='center',verticalalignment='center',fontsize=20, zorder=6)
    
    ############################################################################################################
    # save figure
    if save_yn:
        outputName = outputFolder + 'plateboundaries_' + time_str.zfill(3) + '.png'
        plt.savefig(outputName, dpi=200)
    
    plt.show()
