# -*- coding: utf-8 -*-
"""
Created on Mon Jul 28 18:21:21 2014

@author: Russ
"""

import srtm
import numpy as np

def get_mhot(source_lat,source_lon,source_alt,
             target_lat,target_lon,step_size=100,elevdata=None):
    
        RADIUS = 6366707.0
        KFACTOR = 4/3
        MOD_RADIUS = RADIUS*KFACTOR         
                 
        if elevdata is None:
            elevdata = srtm.get_data(leave_zipped=True)
          
        # get source elevation
        tmp = elevdata.get_elevation(source_lat, source_lon)
        if tmp is None:
            tmp = 0
        source_elev = source_alt + tmp
        
        # convert source to a position vector
        phi = np.deg2rad(90 - source_lat)
        theta = np.deg2rad(source_lon)
        sinphi = np.sin(phi)
        mag_source = MOD_RADIUS+source_elev
        source_vec = mag_source*np.array([sinphi*np.cos(theta), sinphi*np.sin(theta), np.cos(phi)])
        
        # calculate angle needed to rotate vector to achieve step size
        # convert target lat/lon to a position vector
        phi = np.deg2rad(90 - target_lat)
        theta = np.deg2rad(target_lon)
        sinphi = np.sin(phi)
        target_vec = np.array([sinphi*np.cos(theta), sinphi*np.sin(theta), np.cos(phi)])

        
        normal = np.cross(source_vec, target_vec)
        axis = normal/np.linalg.norm(normal)
        ex = source_vec
        ey = np.cross(axis, ex)
        
        
        source_unit_vec = source_vec/np.linalg.norm(source_vec)
        target_unit_vec = target_vec/np.linalg.norm(target_vec)
        dot = np.dot(target_unit_vec,source_unit_vec)
        if np.abs(dot) < 0.8:
            target_angle=np.arccos(dot)
        elif dot > 0:
            diff = source_unit_vec - target_unit_vec
            target_angle = 2.0*np.arcsin(np.linalg.norm(diff)/2.0)
        else:
            summ = source_unit_vec + target_unit_vec
            target_angle = np.pi() - 2.0*np.arcsin(np.linalg.norm(summ)/2.0)
            
            
        current_angle = target_angle
        grnd_dist = target_angle*RADIUS
        num_steps = np.floor(grnd_dist/step_size)+1

        print "grnd_dist =",grnd_dist,", num_steps =",num_steps
        
        step_size = grnd_dist/(num_steps-1)
        
        mod_angle_rot = step_size/MOD_RADIUS
        angle_rot = step_size/RADIUS
     
        current_lat = source_lat
        current_lon = source_lon
        loop_rng = range(1,int(num_steps-1))

        
        if num_steps-1 <=0:
            return elevdata.get_elevation(target_lat,target_lon)
        else:
            for n in loop_rng:
                eadd = (ex*np.cos(n*angle_rot) + ey*np.sin(n*angle_rot))
                current_vec = eadd
                
                radiusval = np.linalg.norm(eadd)
                phi = np.arccos(current_vec[2] / radiusval)
                current_lat = 90 - np.rad2deg(phi)
                arg = current_vec[0] / (radiusval*np.sin(phi))
                if arg > 1:
                    theta = 0
                elif arg < -1:
                    theta = np.pi()
                else:
                    theta = np.arccos(arg)
                
                if current_vec[1]<0:
                    current_lon = np.rad2deg(-theta)
                else:
                    current_lon = np.rad2deg(theta)
                
                eadd = (ex*np.cos(n*mod_angle_rot) + ey*np.sin(n*mod_angle_rot))
                mod_current_vec = eadd
                current_alt = elevdata.get_elevation(current_lat,current_lon)
                if current_alt is None:
                    current_alt = 0
                current_unit = mod_current_vec / np.linalg.norm(mod_current_vec)
                dot = np.dot(current_unit, source_unit_vec)
                current_angle = n*mod_angle_rot
                mag_current = MOD_RADIUS + current_alt
                
                rise_dist = mag_current*np.cos(current_angle)-mag_source       
                run_dist = mag_current*np.sin(current_angle)
                
                if n==1:
                    current_slope = rise_dist/run_dist
                elif (rise_dist/run_dist) > current_slope:
                    current_slope = rise_dist/run_dist
            
            vert_disp = source_alt + (run_dist*current_slope) - mag_current*np.cos(current_angle) + MOD_RADIUS
            vert_angle = np.arctan(current_slope) + np.deg2rad(90)
            masking_ht = vert_disp / np.sin( np.deg2rad(180) - (vert_angle+current_angle) )*np.sin(vert_angle)
            
        return masking_ht


masking_ht = get_mhot(42.647673, -71.253823, 5, 41.9, -72.1)
print "MHOT = ",masking_ht,"(m)"
