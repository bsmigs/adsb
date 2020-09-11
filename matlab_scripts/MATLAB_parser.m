fid = fopen('myADSBFile7.dat','r');
data = textscan(fid, '%s', 'delimiter', '\n');
fclose(fid);
data = data{1};

reduced_data = {};
for kk = 1:numel(data)
    split_data = strsplit(data{kk},',');
    if (str2double(split_data{2}) == 3 || str2double(split_data{2}) == 4)
        reduced_data{end+1} = data{kk};
    end
end

actual_data = [];
used_IDs = [];
for kk = 1:numel(reduced_data)
    tmp = strsplit(reduced_data{kk},',','CollapseDelimiters',0);
    if (~isempty(tmp{15}) && ~isempty(tmp{16}))
 
        flight_ID = tmp{5};
        flight_alt = str2double(tmp{12});
        flight_lat = str2double(tmp{15});
        flight_lon = str2double(tmp{16});
        
        cond = strcmpi(flight_ID, used_IDs);
        if (any(cond))
            actual_data{cond} = [actual_data{cond} ; [flight_lat, flight_lon, flight_alt]];
        else
            actual_data{end+1} = [flight_lat, flight_lon, flight_alt];
            used_IDs{end+1} = flight_ID;
        end
            
    end
end

%% 2D plots
myQTHCoords = [42.647690, -71.253783]; % (lat, lon) in degrees
max_arclen = 0;
figure;
hold on;
for kk = 1:numel(used_IDs)
    data_lon = actual_data{kk}(:,2);
    data_lat = actual_data{kk}(:,1);
    [arclen, az] = distance(data_lat, data_lon, myQTHCoords(1), myQTHCoords(2), referenceEllipsoid('wgs84','km'));
    max_val = max(arclen);
    if (max_val > max_arclen && max_val < 500)
        max_arclen = max_val;
        flight_idx = kk;
    end
    
    plot(data_lon, data_lat, '.', 'MarkerSize', 6);
end
set(gca,'fontsize',16);
plot(myQTHCoords(2), myQTHCoords(1), 'bs', 'MarkerSize', 12, 'MarkerFaceColor', 'b');
plot(-71.0096,42.3656,'rs','MarkerSize', 12, 'MarkerFaceColor', 'r') % Lawrence Municipal Airport, North Andover
plot(-71.1217,42.7169,'rs','MarkerSize', 12, 'MarkerFaceColor', 'r') % Logan, Boston
xlabel('Longitude (deg)');
ylabel('Latitude (deg)');
fprintf('Flight %s has farthest range at %.2f nmi\n', used_IDs{kk}, max_arclen*unitsratio('nm','km'));


%% 3D plots
figure;
hold on;
for kk = 1:numel(used_IDs)
    data_lon = actual_data{kk}(:,2);
    data_lat = actual_data{kk}(:,1);
    data_alt = actual_data{kk}(:,3)/1e3;
    
    plot3(data_lon, data_lat, data_alt, '.', 'MarkerSize', 6);
end
set(gca,'fontsize',16);
plot3(myQTHCoords(2), myQTHCoords(1), 0, 'bs', 'MarkerSize', 12, 'MarkerFaceColor', 'b');
plot3(-71.0096,42.3656, 0,'rs','MarkerSize', 12, 'MarkerFaceColor', 'r') % Lawrence Municipal Airport, North Andover
plot3(-71.1217,42.7169, 0, 'rs','MarkerSize', 12, 'MarkerFaceColor', 'r') % Logan, Boston
xlabel('Longitude (deg)');
ylabel('Latitude (deg)');
zlabel('Altitude, (kft)');


