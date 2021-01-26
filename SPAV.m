function [winners, win_weights] = SPAV(candidates_file, voters_file, new_format)
%SPAV Calculate primaries results for the Israeli Democratic party
%   candidates  - comma delimited file with header:
%       id, gendre ('f'/'m'), name
%   voters (old)- comma delimited file with header:
%       id, candidate_id
%   voters (new)- comma delimited file without header:
%       "can_id1,can_id2,..."

    candidates_table = readtable(candidates_file);

    if new_format
        % read raw data
        tmp = fileread(voters_file);
        % extract lines
        tmp = regexp(tmp,'(\d+,)*\d+','match');
        % extract numbers in each line
        tmp = cellfun(@(x) str2num(char(string(regexp(x,'\d*','match')'))),tmp,'UniformOutput',false)';
        % concat voter's index while reshaping as one long vector
        tmp = cellfun(@(x,idx) [ones(length(x),1)*idx,x],tmp,num2cell(1:length(tmp))','UniformOutput',false);
        voters_array = cell2mat(tmp);
    else
        voters_table = readtable(voters_file);
        voters_array = table2array(voters_table);
    end
    
    candidates_gender = cell2mat(table2cell(candidates_table(:,2)));
    candidates_gender = (candidates_gender=='f') - (candidates_gender=='m');
    candidates_id = table2array(candidates_table(:,1));
    
    % validity checks
    v = zeros(3,1);
    v(1) = size(candidates_table,2) == 3;
    v(2) = size(voters_array,2) == 2;
    v(3) = isempty(find(candidates_gender ~= 1 & candidates_gender ~= -1,1));
%    v(4) = isempty(find(candidates_id ~= (1:length(candidates_id))',1));
    if(find(v==false))
        disp('validity checks failed');
        return
    end

    % initialize variables
    num_candidates = max(candidates_id);
    num_voters = max(voters_array(:,1));
    sz = [num_candidates, num_voters];
    weights = zeros(sz);
    weights(sub2ind(sz,voters_array(:,2),voters_array(:,1))) = 1;
    winners = zeros(num_candidates,1);
    win_weights = zeros(num_candidates,1);
    women_lead = 0;
    candidates_names = table2cell(candidates_table(:,3));
    [~, lex_order] = sort(candidates_names);
    index = 1;
    round_error = 0.0001;
    
    % iterate over winning position
    while(~isempty(find(weights>round_error,1)))
        counter = sum(weights,2);
        
        % remove men if not enough women
        if(women_lead <= 0 && index > 3)
            counter(candidates_id(candidates_gender == -1)) = 0;
        end
        
        % leave only winners
        max_counter = max(counter);
        if(max_counter < round_error)
            break;
        end
        counter(abs(max_counter-counter) > round_error) = 0;
        
        % pick the first in lex order
        winner_lex_order = find(counter(candidates_id(lex_order))>round_error,1);
        winners(index) = candidates_id(lex_order(winner_lex_order));
        win_weights(index) = counter(candidates_id(lex_order(winner_lex_order)));
        women_lead = women_lead + candidates_gender(find(candidates_id == winners(index),1));

        % update weights
        hv = weights(:,weights(winners(index),:)>round_error);
        hv(hv > round_error) = 1./(1./hv(hv > round_error)+1);
        weights(:,weights(winners(index),:)>round_error) = hv;
        % remove winner
        weights(winners(index),:) = 0;
        
        % continue
        index = index + 1;
    end
    
    % pretty print results
    max_name_length = size(char(string(table2cell(candidates_table(:,3)))),2);
    disp(['position, id,   ',sprintf('%-*s',max_name_length+1,'name,'),'  weight']);
    for index = 1:length(winners)
        order = sprintf('%-4s', [num2str(index),':']);
        id = sprintf('%-4s', [num2str(winners(index)),',']);
        win_index = find(candidates_id == winners(index),1);
        name = cell2mat(table2array(candidates_table(win_index, 3)));
        name = sprintf('%-*s',max_name_length+1,[name,',']);
        weight = num2str(win_weights(index));
        disp([order,'      ', id, '  ', name, '  ',weight]);
    end
end

