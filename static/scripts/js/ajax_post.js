// FUNCTION : Audience Reach Poll
window.audienceReachPoll = function(requestID){

    // Set up recurring loop to check audience query every X ms
    setTimeout(function() {

        // add loop counter to set a max
        window.audienceReachPoll_count = window.audienceReachPoll_count || 0; // calculate current loop       
        window.audienceReachPoll_count++ // increase loop count
        window.audienceReachPoll_count_loop_max = 100; // set max loops to run
        window.audienceReachPoll_count_loop_interval = 5000; // Interval between loops

        // check if loop exceeded
        if(window.audienceReachPoll_count_loop_max < window.audienceReachPoll_count){
            window.audienceReachPoll_stoploop = true;
        }

        if (!window.audienceReachPoll_stoploop){

            // Format request data
            request_data = "requestID=" + requestID;

            $.ajax({
                    url: '/audience_reach_poll',
                    data: request_data,
                    type: 'POST',
                    success: function(response) {
                        
                        // Parse response so we can read it
                        response = JSON.parse(response);

                        // If job completed : send back to form
                        if (response.status === "completed"){

                            // Push data into form                            
                            var pretty_data = JSON.stringify(response,undefined,3);                            
                            jQuery("#apiResponse").text(pretty_data);
                            notify_inprogress.dismiss();
                            alertify.notify('Success! Your results are in the box ', 'success', 5);

                            // Stop loop
                            window.audienceReachPoll_stoploop = true; 

                        // If job not completed : try again
                        } else if (response.status.indexOf('not completed') > -1){

                            // Update HTML
                            var pretty_data = JSON.stringify(response,undefined,3);                            
                            jQuery("#apiResponse").text(pretty_data);

                            // Poll again
                            window.audienceReachPoll(requestID);
                        };
                        
                    },
                    error: function(error) {
                        
                        // Stop job
                        console.log("ERROR : See below");
                        console.log(error);
                        window.audienceReachPoll(requestID);                        
                    }
                });
            } else {

                // Polling Stopped                
                notify_inprogress.dismiss(); // remove in progress message
                alertify.error("Query taken too long - this query probably won't work :("); // error message
                jQuery("#apiResponse").text("Query taken too long - this query probably won't work :(");
            }

        
    },window.audienceReachPoll_count_loop_interval);

};

// FUNCTION : Audience Reach Query
window.audienceReachQuery = function(){

        // Reset poll limit
        window.audienceReachPoll_count = 0;
        window.audienceReachPoll_stoploop = false;

        // ALERTIFY : Notifications (requires alertify.js)        
        var alertify_notification = "DATA SUBMITTED:<br><br>";        
        var form_fields_array = $('form').serialize().split('&');
        var form_fields = {};
        var fail = false;
        for (var i = 0; i < form_fields_array.length; i++) {
            var kvp = form_fields_array[i].split('=');
            form_fields[kvp[0]] = kvp[1]
            if (!kvp[1]) {
                fail = true
            };
            alertify_notification = alertify_notification + form_fields_array[i] + "<br>";
        }

        // If data missing
        if (fail) {

            alertify.error('ERROR : Missing Field - please fill in all fields');
            jQuery("#apiResponse").text("Missing Field - please fill in all fields");

        // Otherwise allow data

        } else {
            
            jQuery("#apiResponse").html("<br>Awaiting API results (may take a minute or two (if it fails it will say here))...<br><br>Public Key = " + form_fields.apiPublicKey + "<br>Secret Key = " + form_fields.apiSecretKey);
            window.notify_inprogress = alertify.notify('Request in progress.', 'custom', 1000);
            
            // Join form data to requestID to pass to server
            request_data = $('form').serialize();

            // API Return Response
            $.ajax({
                url: '/audience_reach_queue',
                data: request_data,
                type: 'POST',
                success: function(response) {
                                        
                    // Begin polling API to see if ready (with requestID returned)                                        
                    audienceReachPoll(response);
                },
                error: function(error) {
                    alertify.error(error.statusText + "<br> Check your credentials/category ID");
                    notify_inprogress.dismiss();
                    jQuery("#apiResponse").html("<br>Failure - either credentials are wrong or something is broken (send your category ID to roshan.gonsalkorale@oracle.com)...<br><br>Public Key = " + form_fields.apiPublicKey + "<br>Secret Key = " + form_fields.apiSecretKey + "<br>Category ID = " + form_fields.categoryID);
                }
            });

            
        }

    };

// Add Tracking to form submit
$(function() {
    $('button').click(function(){        
        audienceReachQuery()});
});